/**
 * Email Identity
 *
 * Displays normalized identity information
 * of a parsed email.
 */

function normalizeAddressList(
  addresses,
) {
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

function formatAddressList(addresses) {
  const items =
    normalizeAddressList(addresses);

  if (items.length === 0) {
    return "—";
  }

  return items.join(", ");
}

function IdentityField({
  label,
  value,
  mono = false,
}) {
  const displayValue =
    value !== null &&
    value !== undefined &&
    String(value).trim() !== ""
      ? String(value)
      : "—";

  return (
    <div className="parsing-identity-field">
      <span className="parsing-identity-field__label">
        {label}
      </span>

      <div
        className={
          mono
            ? "parsing-identity-field__value parsing-identity-field__value--mono"
            : "parsing-identity-field__value"
        }
      >
        {displayValue}
      </div>
    </div>
  );
}

export default function EmailIdentity({
  identity = {},
  source,
  sourceIdentifier,
}) {
  const recipients =
    normalizeAddressList(
      identity?.recipients,
    );

  const replyTo =
    normalizeAddressList(
      identity?.reply_to,
    );

  const cc =
    normalizeAddressList(identity?.cc);

  const bcc =
    normalizeAddressList(identity?.bcc);

  return (
    <section className="parsing-detail-card">
      <header className="parsing-detail-card__header">
        <div>
          <span className="parsing-detail-card__eyebrow">
            IDENTITY
          </span>

          <h2>Email Identity</h2>

          <p>
            Normalized sender, recipient and
            message identity information.
          </p>
        </div>
      </header>

      <div className="parsing-identity-grid">
        <IdentityField
          label="Message-ID"
          value={identity?.message_id}
          mono
        />

        <IdentityField
          label="Subject"
          value={identity?.subject}
        />

        <IdentityField
          label="Sender"
          value={identity?.sender}
        />

        <IdentityField
          label="Recipients"
          value={formatAddressList(
            recipients,
          )}
        />

        <IdentityField
          label="Reply-To"
          value={formatAddressList(
            replyTo,
          )}
        />

        <IdentityField
          label="CC"
          value={formatAddressList(cc)}
        />

        <IdentityField
          label="BCC"
          value={formatAddressList(bcc)}
        />

        <IdentityField
          label="Date"
          value={identity?.date}
          mono
        />

        <IdentityField
          label="Source"
          value={source}
        />

        <IdentityField
          label="Source Identifier"
          value={sourceIdentifier}
          mono
        />
      </div>
    </section>
  );
}