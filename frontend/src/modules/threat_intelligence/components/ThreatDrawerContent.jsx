export default function ThreatDrawerContent({ mode, children }) {
  return (
    <div
      className={`ti-drawer-content ti-drawer-content--${mode || "details"}`}
    >
      {children}
    </div>
  );
}
