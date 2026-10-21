import { formatCount } from "../types";

export default function ClassificationDistribution({ items = [] }) {
  const total = items.reduce((sum, item) => sum + Number(item.count || 0), 0);
  return <section className="an-panel"><header className="an-panel-heading"><div><h2>Classification Distribution</h2><p>Predicted labels in the selected range</p></div></header>{items.length ? <div className="an-distribution">{items.map((item) => <div className="an-distribution-row" key={item.classification}><span>{item.classification === "bomb" ? "Bomb" : "Normal"}</span><div className="an-track"><i className={`an-fill an-fill--${item.classification}`} style={{ width: `${total ? Number(item.count || 0) / total * 100 : 0}%` }}/></div><strong>{formatCount(item.count)}</strong></div>)}</div> : <p className="an-empty">No classification records in this range.</p>}</section>;
}
