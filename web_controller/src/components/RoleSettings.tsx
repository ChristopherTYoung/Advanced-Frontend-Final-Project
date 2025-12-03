import { useState } from "react";
import { useGuildRoles } from "../hooks/useApi";

type RoleSettingsProps = {
    selectedGuildId: string | null;
    roleEntries: RoleEntry[];
    setRoleEntries: React.Dispatch<React.SetStateAction<RoleEntry[]>>
    isGuildOwner: boolean;
}
type RoleEntry = {
    role_id?: string;
    role_name: string;
    permissions: { permission_name: string; allowed: boolean }[];
}

export function RoleSettings({selectedGuildId, roleEntries, setRoleEntries, isGuildOwner}: RoleSettingsProps) {
    const [selectedRoleToAdd, setSelectedRoleToAdd] = useState<string>('')
    const { data: guildRoles } = useGuildRoles(selectedGuildId)

    const permissionList = [
        'change_nickname',
        'change_personality',
        'make_events',
        'manage_proposals',
    ]
    function addSelectedRole() {
        if (!selectedRoleToAdd) return
        const roleId = selectedRoleToAdd
        const roleObj = guildRoles?.find((r: { id: string; name: string }) => r.id === roleId)
        const roleName = roleObj?.name || roleId
        if (roleEntries.find((r) => r.role_id === roleId || r.role_name === roleName)) return
        const newEntry: RoleEntry = {
            role_id: roleId,
            role_name: roleName,
            permissions: permissionList.map((p) => ({ permission_name: p, allowed: false })),
        }
        setRoleEntries((prev) => [...prev, newEntry])
    }

    function togglePermission(roleName: string, permissionName: string) {
        setRoleEntries((prev) =>
            prev.map((r) => {
                if (r.role_name !== roleName) return r
                return {
                    ...r,
                    permissions: r.permissions.map((p) =>
                        p.permission_name === permissionName ? { ...p, allowed: !p.allowed } : p
                    ),
                }
            })
        )
    }

    function removeRole(roleName: string) {
        setRoleEntries((prev) => prev.filter((r) => r.role_name !== roleName))
    }
    return (
        <div className="form-group">
            <h3>Role Settings</h3>
            <label htmlFor="role-select">Add Role Permissions:</label>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <select
                    id="role-select"
                    value={selectedRoleToAdd}
                    onChange={(e) => setSelectedRoleToAdd(e.target.value)}
                    disabled={!guildRoles || !isGuildOwner}
                >
                    <option value="">-- Select a Role --</option>
                    {guildRoles?.map((r: { id: string; name: string }) => (
                        <option key={r.id} value={r.id}>{r.name}</option>
                    ))}
                </select>
                <button type="button" onClick={addSelectedRole} disabled={!isGuildOwner}>Add Role</button>
            </div>

            {!isGuildOwner && <p style={{ color: '#666' }}>Only the guild owner can edit role permissions.</p>}
            {roleEntries.length === 0 && <p>No roles configured yet.</p>}

            {roleEntries.map((role) => (
                <div key={role.role_name} className="role-entry" style={{ border: '1px solid #ccc', padding: '8px', marginTop: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong>{role.role_name}</strong>
                        <button type="button" onClick={() => removeRole(role.role_name)} disabled={!isGuildOwner}>Remove</button>
                    </div>
                    <div style={{ display: 'flex', gap: '12px', marginTop: '8px', flexWrap: 'wrap' }}>
                        {role.permissions.map((p) => (
                            <label key={p.permission_name} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                                <input
                                    type="checkbox"
                                    checked={!!p.allowed}
                                    onChange={() => togglePermission(role.role_name, p.permission_name)}
                                    disabled={!isGuildOwner}
                                />
                                {p.permission_name}
                            </label>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    )
}