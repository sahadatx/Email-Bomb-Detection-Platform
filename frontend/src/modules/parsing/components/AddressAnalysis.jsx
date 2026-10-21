/**
 * Address Analysis
 *
 * Presents normalized email address relationships.
 */

function normalizeAddresses(addresses) {
  if (!Array.isArray(addresses)) {
    return [];
  }

  return addresses
    .filter(
      (address) =>
        address !== null &&
        address !== undefined &&
        String(address).trim() !== "",
    )
    .map((address) => String(address).trim());
}

function AddressGroup({ label, addresses = [] }) {
  const items = normalizeAddresses(addresses);

  return (
    <article className="parsing-address-group">
      <header className="parsing-address-group__header">
        <span>{label}</span>
        <strong>{items.length}</strong>
      </header>

      {items.length === 0 ? (
        <div className="parsing-address-empty">
          None
        </div>
      ) : (
        <ul className="parsing-address-list">
          {items.map((address, index) => (
            <li
              key={`${address}-${index}`}
              className="parsing-address-item"
            >
              <span
                className="parsing-address-item__icon"
                aria-hidden="true"
              >
                @
              </span>

              <span>{address}</span>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

export default function AddressAnalysis({
  identity = {},
}) {
  const sender = identity?.sender
    ? [identity.sender]
    : [];

  const recipients = normalizeAddresses(
    identity?.recipients,
  );

  const replyTo = normalizeAddresses(
    identity?.reply_to,
  );

  const cc = normalizeAddresses(
    identity?.cc,
  );

  const bcc = normalizeAddresses(
    identity?.bcc,
  );

  return (
    <section className="parsing-detail-card">
      <header className="parsing-detail-card__header">
        <div>
          <span className="parsing-detail-card__eyebrow">
            ADDRESS ANALYSIS
          </span>

          <h2>Address Analysis</h2>

          <p>
            Normalized sender and recipient
            relationships extracted from the
            message.
          </p>
        </div>
      </header>

      <div className="parsing-address-layout">
        <AddressGroup
          label="From"
          addresses={sender}
        />

        <AddressGroup
          label="To"
          addresses={recipients}
        />

        <AddressGroup
          label="Reply-To"
          addresses={replyTo}
        />

        <AddressGroup
          label="CC"
          addresses={cc}
        />

        <AddressGroup
          label="BCC"
          addresses={bcc}
        />
      </div>
    </section>
  );
}