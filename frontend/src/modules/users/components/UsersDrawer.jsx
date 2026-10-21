import { useEffect, useState } from "react";
import { ArrowLeft, X, UserRound, Shield, KeyRound, LockKeyhole, Monitor, History, Pencil, UserPlus } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import { PERMISSIONS, hasPermission } from "../../../core/permissions/permissions";
import { ROLE_LABELS, USER_ROLES } from "../types";
import { apiRequest } from "../../../core/api/client";
import ErrorNotice from "../../../core/components/ErrorNotice";
import {
  changeUserForcePassword, changeUserRole, createUser, disableUser, enableUser,
  getUser, getUserSessions, lockUser, resetUserPassword, revokeAllUserSessions,
  revokeUserSession, unlockUser, updateUser,
} from "../services/userService";

const ACTIONS = [
  ["details", "View Details", "View profile, sessions and audit history", UserRound, PERMISSIONS.USERS_READ],
  ["edit", "Edit User", "Update user information", Pencil, PERMISSIONS.USERS_UPDATE],
  ["role", "Change Role", "Modify user role", Shield, PERMISSIONS.USERS_ROLE_CHANGE],
  ["password", "Reset Password", "Reset password and force password change", KeyRound, PERMISSIONS.USERS_PASSWORD_RESET],
  ["status", "Enable / Disable", "Change account access", LockKeyhole, null],
  ["sessions", "Manage Sessions", "View and revoke active sessions", Monitor, PERMISSIONS.USERS_READ],
  ["lock", "Lock / Unlock", "Temporarily block account access", LockKeyhole, null],
];

function date(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleString();
}
function message(error) { return error?.message || "The request could not be completed."; }

export default function UsersDrawer({ initialUser, create = false, onClose, onChanged }) {
  const { accessToken, user: actor } = useAuth();
  const [view, setView] = useState(create ? "create" : "actions");
  const [user, setUser] = useState(initialUser || null);
  const [sessions, setSessions] = useState([]);
  const [audit, setAudit] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [form, setForm] = useState({ full_name: "", email: "", username: "", password: "", role: USER_ROLES.VIEWER, is_active: true, force_password_change: true });
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [forceChange, setForceChange] = useState(true);

  useEffect(() => {
    const onKey = (event) => { if (event.key === "Escape" && !saving) onClose(); };
    window.addEventListener("keydown", onKey);
    document.body.classList.add("users-drawer-open");
    return () => { window.removeEventListener("keydown", onKey); document.body.classList.remove("users-drawer-open"); };
  }, [onClose, saving]);

  useEffect(() => {
    if (!user) return;
    setForm({ full_name: user.full_name || "", email: user.email || "", username: user.username || "", password: "", role: user.role, is_active: user.is_active, force_password_change: true });
  }, [user]);

  async function openView(next) {
    setError(""); setSuccess(""); setView(next);
    if (!user?.id) return;
    setLoading(true);
    try {
      if (next === "details") setUser(await getUser(accessToken, user.id));
      if (next === "sessions") setSessions(await getUserSessions(accessToken, user.id));
      if (next === "audit") {
        const result = await apiRequest(`/audit?search=${encodeURIComponent(user.id)}&page=1&page_size=30`, { token: accessToken });
        setAudit(result?.items || []);
      }
    } catch (e) { setError(message(e)); }
    finally { setLoading(false); }
  }
  function back() { setError(""); setSuccess(""); setView(create ? "create" : "actions"); }
  function setField(key, value) { setForm((current) => ({ ...current, [key]: value })); setError(""); }
  async function run(action) {
    setSaving(true); setError(""); setSuccess("");
    try {
      const result = await action();
      if (result?.id) setUser(result);
      setSuccess("Changes saved successfully.");
      onChanged?.();
      if (["create", "edit", "role", "password", "status", "lock"].includes(view)) {
        if (view === "create") { onClose(); return; }
        if (view === "password") { setPassword(""); setConfirmPassword(""); }
        if (view === "status" || view === "lock") back();
      }
    } catch (e) { setError(message(e)); }
    finally { setSaving(false); }
  }
  function submitUser(event) {
    event.preventDefault();
    if (!form.full_name.trim() || !form.email.trim() || !form.username.trim()) return setError("Complete the required account fields.");
    if (create && form.password.length < 12) return setError("Password must contain at least 12 characters.");
    const payload = { full_name: form.full_name.trim(), email: form.email.trim(), username: form.username.trim() };
    if (create) Object.assign(payload, { password: form.password, role: form.role, is_active: form.is_active, force_password_change: form.force_password_change });
    run(async () => {
      if (create) return createUser(accessToken, payload);
      let updated = await updateUser(accessToken, user.id, payload);
      if (form.role !== user.role && allowed(PERMISSIONS.USERS_ROLE_CHANGE)) updated = await changeUserRole(accessToken, user.id, form.role);
      if (Boolean(form.is_active) !== Boolean(user.is_active)) updated = form.is_active ? await enableUser(accessToken, user.id) : await disableUser(accessToken, user.id);
      return updated;
    });
  }
  function submitPassword(event) {
    event.preventDefault();
    if (password.length < 12) return setError("Password must contain at least 12 characters.");
    if (password !== confirmPassword) return setError("Passwords do not match.");
    run(async () => {
      const updated = await resetUserPassword(accessToken, user.id, password);
      if (forceChange !== updated.force_password_change) return changeUserForcePassword(accessToken, user.id, forceChange);
      return updated;
    });
  }
  const allowed = (permission) => permission ? hasPermission(actor, permission) : false;
  const currentStatus = user?.is_active ? "Active" : "Disabled";
  const currentLock = user?.is_locked ? "Locked" : "Unlocked";
  const title = create ? "Create User" : ({ actions: "User Actions", details: "User Details", edit: "Edit User", role: "Change Role", password: "Reset Password", status: user?.is_active ? "Disable User" : "Enable User", sessions: "Manage Sessions", lock: user?.is_locked ? "Unlock User" : "Lock User", audit: "Audit History" }[view] || "User Details");
  const changeStatusPermission = user?.is_active ? PERMISSIONS.USERS_DISABLE : PERMISSIONS.USERS_ENABLE;
  const changeLockPermission = user?.is_locked ? PERMISSIONS.USERS_UNLOCK : PERMISSIONS.USERS_LOCK;

  return <div className="users-drawer-overlay" onMouseDown={(event) => { if (event.target === event.currentTarget && !saving) onClose(); }}>
    <aside className="users-drawer" role="dialog" aria-modal="true" aria-label={title}>
      <header className="users-drawer-header">
        <div className="users-drawer-heading">
          {!create && view !== "actions" && <button className="users-icon-button" type="button" aria-label="Back" onClick={back}><ArrowLeft size={17}/></button>}
          <div><span>USER MANAGEMENT</span><h2>{title}</h2></div>
        </div>
        <button className="users-icon-button" type="button" aria-label="Close" onClick={onClose} disabled={saving}><X size={18}/></button>
      </header>
      <div className="users-drawer-body">
        {create ? <>
          <p className="users-drawer-intro">Create a new platform user account.</p>
          <UserFormFields form={form} setField={setField} create />
          <label className="users-check"><input type="checkbox" checked={form.force_password_change} onChange={(e) => setField("force_password_change", e.target.checked)}/> Force password change on first login</label>
        </> : <>
          <div className="users-drawer-profile"><div className="users-drawer-avatar">{(user?.full_name || user?.username || "U").slice(0,1).toUpperCase()}</div><div><strong>{user?.full_name}</strong><span>{user?.email}</span><div className="users-profile-tags"><b>{user?.role}</b><i className={user?.is_active ? "good" : "muted"}>{currentStatus}</i><i className={user?.is_locked ? "bad" : "good"}>{currentLock}</i></div></div></div>
          {view === "actions" && <><div className="users-action-label">ACCOUNT ACTIONS</div><div className="users-action-list">{ACTIONS.map(([id, label, detail, Icon, permission]) => {
            const permitted = id === "status" ? allowed(changeStatusPermission) : id === "lock" ? allowed(changeLockPermission) : allowed(permission);
            if (!permitted) return null;
            return <button type="button" key={id} className="users-action-item" onClick={() => id === "status" || id === "lock" ? openView(id) : openView(id)}><Icon size={17}/><span><strong>{id === "status" ? `${user?.is_active ? "Disable" : "Enable"} User` : id === "lock" ? `${user?.is_locked ? "Unlock" : "Lock"} User` : label}</strong><small>{detail}</small></span><b>›</b></button>;
          })}</div></>}
          {view === "details" && <><div className="users-tabs"><button className="active">Overview</button><button onClick={() => openView("sessions")}>Sessions</button><button onClick={() => openView("audit")}>Audit History</button></div><section className="users-drawer-section"><h3>Account Information</h3><Detail label="Full Name" value={user?.full_name}/><Detail label="Email" value={user?.email}/><Detail label="Username" value={user?.username}/><Detail label="Role" value={user?.role}/><Detail label="Account Status" value={currentStatus}/><Detail label="Lock Status" value={currentLock}/><Detail label="Created At" value={date(user?.created_at)}/><Detail label="Last Login" value={date(user?.last_login_at)}/></section><div className="users-quick-actions">{[["edit","Edit User",PERMISSIONS.USERS_UPDATE],["role","Change Role",PERMISSIONS.USERS_ROLE_CHANGE],["password","Reset Password",PERMISSIONS.USERS_PASSWORD_RESET],["sessions","Sessions",PERMISSIONS.USERS_READ]].filter((x) => allowed(x[2])).map(([id,label])=><button type="button" key={id} onClick={()=>openView(id)}>{label}</button>)}</div></>}
          {view === "edit" && <><p className="users-drawer-intro">Update the selected user's account information.</p><UserFormFields form={form} setField={setField}/>{allowed(PERMISSIONS.USERS_ROLE_CHANGE)&&<label className="users-drawer-field">Role<select value={form.role} onChange={(e)=>setField("role",e.target.value)}>{Object.values(USER_ROLES).map((role)=><option key={role} value={role}>{ROLE_LABELS[role]}</option>)}</select></label>}{allowed(user?.is_active?PERMISSIONS.USERS_DISABLE:PERMISSIONS.USERS_ENABLE)&&<label className="users-drawer-field">Account Status<select value={form.is_active?"active":"disabled"} onChange={(e)=>setField("is_active",e.target.value==="active")}><option value="active">Active</option><option value="disabled">Disabled</option></select></label>}<p className="users-hint">Password changes are managed through Reset Password to ensure the backend records the required security state.</p></>}
          {view === "role" && <><p className="users-drawer-intro">Change the role assigned to this user.</p><div className="users-callout"><b>Selected User</b><span>{user?.full_name}</span><small>Current role: {user?.role}</small></div><label className="users-drawer-field">New Role<select value={form.role} onChange={(e)=>setField("role",e.target.value)}>{Object.values(USER_ROLES).map((role)=><option key={role} value={role}>{role}</option>)}</select></label><p className="users-hint">Changing a role changes the user's permissions. Confirm that the new role is appropriate.</p></>}
          {view === "password" && <form onSubmit={submitPassword}><p className="users-drawer-intro">Reset the password for this user. Password values are never returned by the API.</p><label className="users-drawer-field">New Password<input type="password" autoComplete="new-password" minLength={12} maxLength={128} value={password} onChange={(e)=>setPassword(e.target.value)} required/><small>Use 12–128 characters with at least one uppercase letter, one lowercase letter, one number, and one special character.</small></label><label className="users-drawer-field">Confirm Password<input type="password" autoComplete="new-password" minLength={12} maxLength={128} value={confirmPassword} onChange={(e)=>setConfirmPassword(e.target.value)} required/></label><label className="users-check"><input type="checkbox" checked={forceChange} onChange={(e)=>setForceChange(e.target.checked)}/> Force password change on next login</label></form>}
          {(view === "status" || view === "lock") && <><p className="users-drawer-intro">Confirm this account access change.</p><div className="users-callout"><b>{user?.full_name}</b><span>{user?.email}</span><small>Current {view === "status" ? "status" : "lock status"}: {view === "status" ? currentStatus : currentLock}</small></div><h3 className="users-confirm-title">{view === "status" ? `${user?.is_active ? "Disable" : "Enable"} this account?` : `${user?.is_locked ? "Unlock" : "Lock"} this user?`}</h3><p className="users-hint">{view === "status" ? "Disabling prevents sign in. Revoke active sessions separately when necessary." : "A locked account cannot sign in until it is unlocked."}</p></>}
          {view === "sessions" && <><p className="users-drawer-intro">View and revoke active sessions for this user.</p><h3 className="users-session-count">{sessions.filter((s)=>!s.revoked_at && new Date(s.expires_at)>new Date()).length} active sessions</h3>{sessions.length ? sessions.map((session)=><div className="users-session-card" key={session.id}><Monitor size={17}/><div><strong>{session.user_agent || "Unknown device"}</strong><span>{session.ip_address || "IP unavailable"}</span><small>Last active: {date(session.created_at)} · Expires {date(session.expires_at)}</small></div>{!session.revoked_at && new Date(session.expires_at)>new Date() && allowed(PERMISSIONS.USERS_UPDATE) && <button type="button" onClick={()=>run(async()=>{await revokeUserSession(accessToken,user.id,session.id); setSessions((items)=>items.map((item)=>item.id===session.id?{...item,revoked_at:new Date().toISOString()}:item)); return null;})}>Revoke</button>}</div>) : !loading && <div className="users-drawer-empty">No sessions have been recorded for this user.</div>}{sessions.some((s)=>!s.revoked_at && new Date(s.expires_at)>new Date()) && allowed(PERMISSIONS.USERS_UPDATE) && <button className="users-danger-wide" type="button" disabled={saving} onClick={()=>run(async()=>{await revokeAllUserSessions(accessToken,user.id); setSessions((items)=>items.map((item)=>item.revoked_at?item:{...item,revoked_at:new Date().toISOString()})); return null;})}>Revoke All Sessions</button>}</>}
          {view === "audit" && <><p className="users-drawer-intro">Recent audit events associated with this user.</p>{audit.length ? audit.map((item)=><article className="users-audit-item" key={item.id}><History size={15}/><div><strong>{item.action}</strong><span>{item.actor_name || "System"} · {item.source || "—"}</span><small>{date(item.created_at)} · {item.status}</small></div></article>) : !loading && <div className="users-drawer-empty">No related audit events found, or your account cannot read audit history.</div>}</>}
        </>}
        {loading && <div className="users-drawer-loading">Loading…</div>}
        {error && <ErrorNotice className="users-drawer-error" title={create ? "User could not be created" : "Action could not be completed"} message={error} />}
        {success && <div className="users-drawer-success" role="status">{success}</div>}
      </div>
      <footer className="users-drawer-footer">
        <button type="button" className="secondary-button" onClick={view === "actions" || create ? onClose : back} disabled={saving}>{view === "actions" || create ? "Close" : "Cancel"}</button>
        {create && <button type="button" className="primary-button" disabled={saving} onClick={submitUser}>{saving?"Creating…":"Create User"}</button>}
        {view === "edit" && <button type="button" className="primary-button" disabled={saving} onClick={submitUser}>{saving?"Saving…":"Save Changes"}</button>}
        {view === "role" && <button type="button" className="primary-button" disabled={saving || form.role===user?.role} onClick={()=>run(()=>changeUserRole(accessToken,user.id,form.role))}>{saving?"Saving…":"Save Role"}</button>}
        {view === "password" && <button type="button" className="primary-button" disabled={saving} onClick={submitPassword}>{saving?"Resetting…":"Reset Password"}</button>}
        {view === "status" && <button type="button" className="danger-button" disabled={saving} onClick={()=>run(()=>user.is_active?disableUser(accessToken,user.id):enableUser(accessToken,user.id))}>{saving?"Updating…":user.is_active?"Disable User":"Enable User"}</button>}
        {view === "lock" && <button type="button" className="danger-button" disabled={saving} onClick={()=>run(()=>user.is_locked?unlockUser(accessToken,user.id):lockUser(accessToken,user.id))}>{saving?"Updating…":user.is_locked?"Unlock User":"Lock User"}</button>}
      </footer>
    </aside>
  </div>;
}

function UserFormFields({ form, setField, create=false }) {
  return <div className="users-drawer-form"><label className="users-drawer-field">Full Name<input value={form.full_name} onChange={(e)=>setField("full_name",e.target.value)} required autoComplete="name"/></label><label className="users-drawer-field">Email<input type="email" value={form.email} onChange={(e)=>setField("email",e.target.value)} required autoComplete="email"/></label><label className="users-drawer-field">Username<input value={form.username} onChange={(e)=>setField("username",e.target.value)} required autoComplete="username" minLength={3}/></label>{create&&<><label className="users-drawer-field">Password<input type="password" value={form.password} onChange={(e)=>setField("password",e.target.value)} required minLength={12} maxLength={128} autoComplete="new-password"/><small>Use 12–128 characters with at least one uppercase letter, one lowercase letter, one number, and one special character.</small></label><label className="users-drawer-field">Role<select value={form.role} onChange={(e)=>setField("role",e.target.value)}>{Object.values(USER_ROLES).map((role)=><option key={role} value={role}>{ROLE_LABELS[role]}</option>)}</select></label></>}</div>;
}
function Detail({label,value}) { return <div className="users-drawer-detail"><span>{label}</span><strong>{value || "—"}</strong></div>; }
