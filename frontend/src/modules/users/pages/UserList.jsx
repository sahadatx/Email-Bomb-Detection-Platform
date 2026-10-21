import { useCallback, useEffect, useState } from "react";
import { MoreVertical, RefreshCw, Users, UserCheck, UserX, LockKeyhole, UserPlus } from "lucide-react";
import { useAuth } from "../../../core/auth/AuthProvider";
import ErrorNotice from "../../../core/components/ErrorNotice";
import Can from "../../../core/permissions/Can";
import { PERMISSIONS } from "../../../core/permissions/permissions";
import { getUserSummary, getUsers } from "../services/userService";
import UsersDrawer from "../components/UsersDrawer";
import { ROLE_LABELS } from "../types";
import "./UserList.css";
import "../styles/users-drawer.css";

const PAGE_SIZE = 30;
function shortDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
}

export default function UserList() {
  const { accessToken } = useAuth();
  const [users, setUsers] = useState([]);
  const [summary, setSummary] = useState({ total: 0, active: 0, disabled: 0, locked: 0 });
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [locked, setLocked] = useState("");
  const [drawerUser, setDrawerUser] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async (nextPage = page) => {
    if (!accessToken) { setError("Sign in to manage user accounts."); setLoading(false); return; }
    setLoading(true); setError("");
    const query = { page: nextPage, pageSize: PAGE_SIZE, search, role, isActive: status === "" ? undefined : status === "active", isLocked: locked === "" ? undefined : locked === "locked" };
    try {
      const [response, counts] = await Promise.all([getUsers(accessToken, query), getUserSummary(accessToken)]);
      setUsers(response?.items || []); setPage(response?.page || nextPage); setPages(response?.pages || 0); setTotal(response?.total || 0); setSummary(counts || { total: 0, active: 0, disabled: 0, locked: 0 });
    } catch (requestError) { setError(requestError?.message || "Unable to load users."); setUsers([]); setSummary({ total: 0, active: 0, disabled: 0, locked: 0 }); }
    finally { setLoading(false); }
  }, [accessToken, page, search, role, status, locked]);

  useEffect(() => {
    const timeout = window.setTimeout(() => { setPage(1); load(1); }, search ? 300 : 0);
    return () => window.clearTimeout(timeout);
  }, [search, role, status, locked, accessToken]);
  useEffect(() => { if (page !== 1) load(page); }, [page]);

  function resetFilters() { setSearch(""); setRole(""); setStatus(""); setLocked(""); setPage(1); }
  const openCreate = () => { setDrawerUser(null); setCreateOpen(true); };
  const closeDrawer = useCallback(() => { setDrawerUser(null); setCreateOpen(false); }, []);

  return <main className="users-page"><div className="users-container">
    <header className="users-page-header"><div><span className="users-eyebrow">SYSTEM ADMINISTRATION</span><h1>Users</h1><p>Manage platform user accounts, roles and access.</p></div><Can permission={PERMISSIONS.USERS_CREATE}><button className="primary-button" type="button" onClick={openCreate}><UserPlus size={16}/> Create User</button></Can></header>
    <section className="users-summary">
      <Summary icon={Users} label="Total Users" value={summary.total}/><Summary icon={UserCheck} label="Active Users" value={summary.active}/><Summary icon={UserX} label="Disabled Users" value={summary.disabled}/><Summary icon={LockKeyhole} label="Locked Users" value={summary.locked}/>
    </section>
    <section className="users-panel">
      <div className="users-filter-heading"><div><strong>Filters</strong><span>Results update automatically when filters change.</span></div></div>
      <div className="users-filters users-filters-inline">
        <div className="users-search"><label htmlFor="user-search">Search Users</label><input id="user-search" type="search" value={search} onChange={(e)=>setSearch(e.target.value)} placeholder="Name, username, or email…"/></div>
        <div className="users-filter-field"><label htmlFor="user-role-filter">Role</label><select id="user-role-filter" className="users-filter-select" value={role} onChange={(e)=>{setRole(e.target.value);setPage(1);}}><option value="">All roles</option>{Object.entries(ROLE_LABELS).map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></div>
        <div className="users-filter-field"><label htmlFor="user-status-filter">Status</label><select id="user-status-filter" className="users-filter-select" value={status} onChange={(e)=>{setStatus(e.target.value);setPage(1);}}><option value="">All statuses</option><option value="active">Active</option><option value="disabled">Disabled</option></select></div>
        <div className="users-filter-field"><label htmlFor="user-lock-filter">Lock Status</label><select id="user-lock-filter" className="users-filter-select" value={locked} onChange={(e)=>{setLocked(e.target.value);setPage(1);}}><option value="">All</option><option value="unlocked">Unlocked</option><option value="locked">Locked</option></select></div>
      </div>
      <div className="users-filter-actions"><button type="button" className="secondary-button" onClick={resetFilters}>Reset Filters</button></div>
      <div className="users-list-heading"><div><h2>User List</h2><span>{total.toLocaleString()} users · {PAGE_SIZE} per page</span></div><button className="users-refresh" type="button" onClick={()=>load(page)} disabled={loading}><RefreshCw size={15}/> Refresh</button></div>
      {error && <ErrorNotice className="users-error" title="Users could not be loaded" message={error} onRetry={()=>load(page)} />}
      {loading ? <div className="users-loading"><div className="loading-spinner"/><span>Loading users…</span></div> : !error && users.length === 0 ? <div className="users-empty"><div className="users-empty-icon">♙</div><h3>No users found</h3><p>No accounts match the selected filters.</p></div> : !error && <div className="users-table-wrapper"><table className="users-table"><thead><tr><th>User</th><th>Role</th><th>Status</th><th>Lock</th><th>Last Login</th><th>Actions</th></tr></thead><tbody>{users.map((user)=><tr key={user.id}><td><div className="user-cell"><div className="user-avatar">{(user.full_name||user.username||"U").slice(0,1).toUpperCase()}</div><div className="user-identity"><strong>{user.full_name}</strong><span>{user.email}</span><small>@{user.username}</small></div></div></td><td><span className="user-role-badge">{user.role}</span></td><td><span className={`users-state-pill ${user.is_active?"is-active":"is-disabled"}`}>{user.is_active?"Active":"Disabled"}</span></td><td><span className={`users-state-pill ${user.is_locked?"is-locked":"is-active"}`}>{user.is_locked?"Locked":"Unlocked"}</span></td><td>{shortDate(user.last_login_at)}</td><td><button className="users-icon-button users-row-menu" type="button" aria-label={`Actions for ${user.full_name}`} onClick={()=>{setDrawerUser(user);setCreateOpen(false);}}><MoreVertical size={19}/></button></td></tr>)}</tbody></table></div>}
      {!loading&&!error&&<footer className="email-pagination" aria-label="Users pagination"><div className="email-pagination-summary"><span>{total===0?"0":`${((page-1)*PAGE_SIZE)+1} - ${Math.min(page*PAGE_SIZE,total)}`}</span><span>/ Total {total.toLocaleString()}</span></div><div className="email-pagination-controls"><button type="button" className="email-pagination-button" aria-label="Go to previous page" disabled={page<=1} onClick={()=>setPage((p)=>Math.max(1,p-1))}><span aria-hidden="true">‹</span>Previous</button><span className="email-pagination-page">Page <strong>{page}</strong> of <strong>{Math.max(1,pages)}</strong></span><button type="button" className="email-pagination-button" aria-label="Go to next page" disabled={!pages||page>=pages} onClick={()=>setPage((p)=>Math.min(pages,p+1))}>Next<span aria-hidden="true">›</span></button></div></footer>}
    </section>
  </div>
  {(drawerUser||createOpen)&&<UsersDrawer key={createOpen?"create":drawerUser?.id} initialUser={drawerUser} create={createOpen} onClose={closeDrawer} onChanged={()=>load(page)}/>}
  </main>;
}
function Summary({icon:Icon,label,value}) { return <article className="summary-card"><span><i><Icon size={16}/></i>{label}</span><strong>{Number(value||0).toLocaleString()}</strong></article>; }
