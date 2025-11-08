import httpx
import json
from typing import Optional, Dict, Any, List, Callable


class LLMService:
    """Service for generating responses using an LLM."""

    def __init__(self, base_url: str = "http://ai-snow.reindeer-pinecone.ts.net:9292/v1", model: str = "gpt-oss-120b"):
        self.base_url = base_url
        self.model = model
        self.timeout = 30.0  # 30 second timeout
        self.tools: List[Dict[str, Any]] = []
        self.tool_functions: Dict[str, Callable] = {}

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], function: Callable):
        tool_definition = {
            "type": "function",
            "function": {"name": name, "description": description, "parameters": parameters},
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
            # Build messages array
            messages = []

            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
            }

            # Add tools if enabled and available
            if use_tools and self.tools:
                payload["tools"] = self.tools
                payload["tool_choice"] = "auto"

            # Make request to LLM
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload)

                if response.status_code == 200:
                    data = response.json()

                    if "choices" not in data or len(data["choices"]) == 0:
                        print(f"ERROR: Unexpected LLM response format: {data}")
                        return None

                    choice = data["choices"][0]
                    message_response = choice.get("message", {})

                    # Check if LLM wants to call a tool
                    if use_tools and "tool_calls" in message_response:
                        tool_calls = message_response["tool_calls"]
                        print(f"DEBUG: LLM requested {len(tool_calls)} tool call(s)")

                        # Add assistant's message with tool calls to history
                        messages.append(message_response)

                        # Execute each tool call
                        for tool_call in tool_calls:
                            function_name = tool_call["function"]["name"]
                            function_args = json.loads(tool_call["function"]["arguments"])
                            tool_call_id = tool_call["id"]

                            print(f"DEBUG: Executing tool '{function_name}' with args: {function_args}")
                            tool_result = await self.execute_tool_call(function_name, function_args)

                            # Add tool result to messages
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call_id,
                                    "name": function_name,
                                    "content": json.dumps(tool_result),
                                }
                            )

                        # Make a second request with the tool results
                        payload["messages"] = messages
                        second_response = await client.post(f"{self.base_url}/chat/completions", json=payload)

                        if second_response.status_code == 200:
                            second_data = second_response.json()
                            if "choices" in second_data and len(second_data["choices"]) > 0:
                                return second_data["choices"][0]["message"]["content"]
                            else:
                                print(f"ERROR: Unexpected second LLM response format: {second_data}")
                                return None
                        else:
                            print(
                                f"ERROR: Second LLM request returned status {second_response.status_code}: {second_response.text}"
                            )
                            return None

                    # No tool calls, return regular response
                    return message_response.get("content")
                else:
                    print(f"ERROR: LLM API returned status {response.status_code}: {response.text}")
                    return None

        except httpx.TimeoutException:
            print("ERROR: LLM request timed out")
            return None
        except Exception as e:
            print(f"ERROR calling LLM: {e}")
            import traceback

            traceback.print_exc()
            return None

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
        personality: Optional[str] = None
    ) -> Optional[str]:
        # Build personality instruction if provided
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
            # Build context about the current server
            server_context = f"You are currently in the server '{guild_name}' (ID: {guild_id})" if guild_name and guild_id else "You are in a Discord server"
            channel_context = f" in the channel #{channel_name}" if channel_name else ""
            
            system_prompt = (
                f"You are a helpful Discord bot assistant. {server_context}{channel_context}. "
                f"You're responding to {username}. Be friendly, helpful, and conversational. "
                "Keep responses concise and appropriate for Discord chat. "
                f"When users ask about 'this server' or 'channels here', they mean guild ID {guild_id}. "
                "You have access to tools:\n"
                "- get_guilds: Get list of all servers the bot is in\n"
                f"- get_channels: Get channels in a specific server (use guild_id: '{guild_id}' for this server)\n"
                f"- get_message_history: Get recent message history"
                f"{personality_instruction}"
            )

        return await self.generate_response(
            user_message, 
            conversation_history=conversation_history,
            system_prompt=system_prompt, 
            use_tools=use_tools
        )

# Singleton instance
llm_service = LLMService()