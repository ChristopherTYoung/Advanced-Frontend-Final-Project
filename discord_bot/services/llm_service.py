import httpx
import json
from typing import Optional, Dict, Any, List, Callable


class LLMService:
    def __init__(self, base_url: str = "http://ai-snow.reindeer-pinecone.ts.net:9292/v1", model: str = "gemma3-27b"):
        self.base_url = base_url
        self.model = model
        self.timeout = 180.0  # 180 second timeout for large model responses with tool calling
        self.tools: List[Dict[str, Any]] = []
        self.tool_functions: Dict[str, Callable] = {}

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], function: Callable):
        tool_definition = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        self.tools.append(tool_definition)
        self.tool_functions[name] = function
        print(f"DEBUG: Registered tool '{name}'")

    async def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        if tool_name not in self.tool_functions:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            function = self.tool_functions[tool_name]
            result = await function(**arguments)
            return result
        except Exception as e:
            print(f"ERROR executing tool '{tool_name}': {e}")
            import traceback

            traceback.print_exc()
            return {"error": str(e)}

    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        use_tools: bool = False,
    ) -> Optional[str]:
        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            if conversation_history:
                for msg in conversation_history:
                    if msg["role"] == "user":
                        if not messages or messages[-1]["role"] != "user":
                            messages.append(msg)
                    else:
                        if messages and messages[-1]["role"] == "user":
                            messages.append(msg)

            if messages and messages[-1]["role"] == "user":
                messages[-1] = {"role": "user", "content": user_message}
            else:
                messages.append({"role": "user", "content": user_message})

            # Debug: Print message structure
            print(f"DEBUG: Message structure being sent:")
            for i, msg in enumerate(messages):
                print(f"  [{i}] role={msg['role']}, content_preview={msg['content'][:50]}...")

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 300,
            }

            if use_tools and self.tools:
                payload["tools"] = self.tools
                payload["tool_choice"] = "auto"
                # Increase max_tokens for tool calling to ensure complete responses
                payload["max_tokens"] = 400
                print(f"DEBUG: Sending {len(self.tools)} tools to LLM")
                print(f"DEBUG: First tool structure: {json.dumps(self.tools[0], indent=2)}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload)

                if response.status_code == 200:
                    data = response.json()

                    if "choices" not in data or len(data["choices"]) == 0:
                        print(f"ERROR: Unexpected LLM response format: {data}")
                        return None

                    choice = data["choices"][0]
                    message_response = choice.get("message", {})

                    if use_tools and "tool_calls" in message_response:
                        max_rounds = 3
                        round_idx = 0

                        messages.append(message_response)

                        while round_idx < max_rounds and "tool_calls" in message_response:
                            tool_calls = message_response.get("tool_calls", [])
                            print(f"DEBUG: LLM requested {len(tool_calls)} tool call(s) in round {round_idx}")

                            for tool_call in tool_calls:
                                function_name = tool_call.get("name") or tool_call.get("function", {}).get("name")
                                raw_args = tool_call.get("arguments") or tool_call.get("function", {}).get(
                                    "arguments", "{}"
                                )
                                try:
                                    function_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                                except Exception:
                                    function_args = {"arguments": raw_args}
                                tool_call_id = tool_call.get("id")

                                print(f"DEBUG: Executing tool '{function_name}' with args: {function_args}")
                                tool_result = await self.execute_tool_call(function_name, function_args)

                                try:
                                    tool_content = json.dumps(tool_result)
                                except Exception:
                                    try:
                                        tool_content = json.dumps(tool_result, default=str)
                                    except Exception:
                                        tool_content = json.dumps({"result": str(tool_result)})

                                messages.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": tool_call_id,
                                        "name": function_name,
                                        "content": tool_content,
                                    }
                                )

                            payload["messages"] = messages
                            follow = await client.post(f"{self.base_url}/chat/completions", json=payload)
                            if follow.status_code != 200:
                                print(
                                    f"ERROR: Follow-up LLM request returned status {follow.status_code}: {follow.text}"
                                )
                                return None

                            follow_data = follow.json()
                            print(f"DEBUG: Follow-up LLM response (round {round_idx}): {follow_data}")

                            if "choices" not in follow_data or len(follow_data["choices"]) == 0:
                                print(f"ERROR: Unexpected follow-up LLM response format: {follow_data}")
                                return None

                            choice = follow_data["choices"][0]
                            message_response = choice.get("message", {})
                            round_idx += 1

                        final_msg = message_response if isinstance(message_response, dict) else None
                        content = None
                        if final_msg:
                            content = final_msg.get("content") or final_msg.get("text")
                            if not content:
                                reasoning = final_msg.get("reasoning_content") or final_msg.get("reasoning")
                                if reasoning:
                                    return reasoning

                        if content is not None:
                            return content

                        try:
                            last_tool_msg = None
                            for m in reversed(messages):
                                if isinstance(m, dict) and m.get("role") == "tool":
                                    last_tool_msg = m
                                    break

                            if last_tool_msg:
                                tool_content = last_tool_msg.get("content")
                                try:
                                    parsed = json.loads(tool_content)
                                except Exception:
                                    parsed = None

                                if isinstance(parsed, dict):
                                    if parsed.get("success") and parsed.get("proposal_id"):
                                        return f"Proposal created (id: {parsed.get('proposal_id')})"
                                    if parsed.get("success") and parsed.get("message"):
                                        return str(parsed.get("message"))
                                    return json.dumps(parsed)
                                elif tool_content is not None:
                                    return str(tool_content)[:1000]
                        except Exception:
                            pass
                        return None

                    return message_response.get("content")
                else:
                    print(f"ERROR: LLM API returned status {response.status_code}: {response.text}")
                    return None

        except httpx.TimeoutException as e:
            print(f"ERROR: LLM request timed out after {self.timeout} seconds: {e}")
            return "I apologize, but I'm taking too long to process your request. The AI model might be overloaded. Please try again in a moment."
        except httpx.ConnectError as e:
            print(f"ERROR: Failed to connect to LLM server: {e}")
            return "I'm unable to respond right now. Please try again later."
        except Exception as e:
            print(f"ERROR: Unexpected error in LLM service: {e}")
            import traceback

            traceback.print_exc()
            return "An unexpected error occurred. Please try again."

    async def moderate_content(self, content: str, image_url: Optional[str] = None) -> Dict[str, Any]:
        prompt = f"""Analyze this content for offensive, inappropriate, or harmful material. 
Rate it on a scale of 0-10 where:
- 0-2: Safe for all ages, no issues
- 3-4: Mild content, minor concerns
- 5-6: Moderate content, some inappropriate language or themes
- 7-8: Mature content, explicit language or adult themes
- 9-10: Highly offensive, harmful, or illegal content

Content to analyze: "{content}"

Respond ONLY with a JSON object in this exact format:
{{"score": <number 0-10>, "issues": ["issue1", "issue2"], "reasoning": "brief explanation"}}"""

        if image_url:
            prompt += f"\n\nImage URL: {image_url}\nNote: Analyze both text and image content."

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 300,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload)

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    content_text = data["choices"][0].get("message", {}).get("content", "")

                    try:
                        if "```json" in content_text:
                            content_text = content_text.split("```json")[1].split("```")[0].strip()
                        elif "```" in content_text:
                            content_text = content_text.split("```")[1].split("```")[0].strip()

                        result = json.loads(content_text)

                        return {
                            "score": int(result.get("score", 0)),
                            "issues": result.get("issues", []),
                            "reasoning": result.get("reasoning", ""),
                        }
                    except json.JSONDecodeError:
                        print(f"ERROR: Failed to parse moderation response as JSON: {content_text}")
                        score = 0
                        if "score" in content_text.lower():
                            import re

                            match = re.search(r'score["\s:]+(\d+)', content_text.lower())
                            if match:
                                score = int(match.group(1))
                        return {"score": score, "issues": [], "reasoning": "Parse error"}
                else:
                    print(f"ERROR: Moderation API returned status {response.status_code}")
                    return {"score": 0, "issues": [], "reasoning": "API error"}

    async def generate_discord_response(
        self,
        user_message: str,
        username: str,
        is_dm: bool = False,
        channel_name: str = None,
        guild_id: str = None,
        guild_name: str = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_tools: bool = True,
        personality: Optional[str] = None,
    ) -> Optional[str]:
        personality_instruction = ""
        if personality:
            personality_instruction = f"\n\nIMPORTANT PERSONALITY: {personality}\nYou MUST respond according to this personality in all your messages."

        if is_dm:
            system_prompt = (
                "You are a helpful Discord bot assistant. You're having a direct message conversation "
                f"with {username}. Be friendly, helpful, and conversational. Keep responses concise "
                "and appropriate for Discord chat. You have access to tools to get information about "
                f"Discord servers and channels.{personality_instruction}"
            )
        else:
            server_context = (
                f"You are currently in the server '{guild_name}' (ID: {guild_id})"
                if guild_name and guild_id
                else "You are in a Discord server"
            )
            channel_context = f" in the channel #{channel_name}" if channel_name else ""

            system_prompt = (
                f"You are a helpful Discord bot assistant. {server_context}{channel_context}. "
                f"You're responding to {username}. Be friendly, helpful, and conversational. "
                "Keep responses concise and appropriate for Discord chat. "
                f"When users ask about 'this server' or 'channels here', they mean guild ID {guild_id}. "
                "You have access to tools:\n"
                "- get_guilds: Get list of all servers the bot is in\n"
                f"- get_channels: Get channels in a specific server (use guild_id: '{guild_id}' for this server)\n"
                f"- get_message_history: Get recent message history\n"
                f"- propose_event: Create an event proposal. IMPORTANT: You must include the username parameter with the value '{username}' when calling this tool.\n"
                f"{personality_instruction}"
            )

        return await self.generate_response(
            user_message, conversation_history=conversation_history, system_prompt=system_prompt, use_tools=use_tools
        )

    def build_system_prompt(self, personality: Optional[str] = None, use_tools: bool = False) -> str:
        personality_text = ""
        if personality:
            personality_text = f"\n\nIMPORTANT PERSONALITY: {personality}\nYou MUST respond according to this personality in all your messages."

        if use_tools:
            return (
                "You are an assistant that can call tools to interact with Discord. "
                "You may either: 1) call the `send_message` tool with arguments {guild_id, channel_id, message} to send a message, OR 2) return plain text in your assistant response which will be sent as-is to the channel. "
                "Prefer concise, friendly announcements suitable for @everyone pings." + personality_text
            )
        else:
            return (
                "You are a Discord announcement generator. Produce a concise, friendly announcement suitable for @everyone pings."
                + personality_text
            )


llm_service = LLMService()
