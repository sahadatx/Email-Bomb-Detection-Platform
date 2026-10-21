const QUEUE_STATUS = Object.freeze({
  QUEUED: "queued",
  PROCESSING: "processing",
  PARSED: "parsed",
  WARNING: "warning",
  FAILED: "failed",
});

function normalizeStatus(status) {
  const value = String(
    status || "",
  ).toLowerCase();

  switch (value) {
    case QUEUE_STATUS.QUEUED:
      return QUEUE_STATUS.QUEUED;

    case QUEUE_STATUS.PROCESSING:
      return QUEUE_STATUS.PROCESSING;

    case QUEUE_STATUS.PARSED:
      return QUEUE_STATUS.PARSED;

    case QUEUE_STATUS.WARNING:
      return QUEUE_STATUS.WARNING;

    case QUEUE_STATUS.FAILED:
      return QUEUE_STATUS.FAILED;

    default:
      return QUEUE_STATUS.QUEUED;
  }
}

function getQueueStatusLabel(status) {
  switch (normalizeStatus(status)) {
    case QUEUE_STATUS.QUEUED:
      return "Queued";

    case QUEUE_STATUS.PROCESSING:
      return "Processing";

    case QUEUE_STATUS.PARSED:
      return "Parsed";

    case QUEUE_STATUS.WARNING:
      return "Warning";

    case QUEUE_STATUS.FAILED:
      return "Failed";

    default:
      return "Queued";
  }
}

function getQueueStatusClass(status) {
  switch (normalizeStatus(status)) {
    case QUEUE_STATUS.PARSED:
      return "parsing-queue-status parsing-queue-status--parsed";

    case QUEUE_STATUS.WARNING:
      return "parsing-queue-status parsing-queue-status--warning";

    case QUEUE_STATUS.FAILED:
      return "parsing-queue-status parsing-queue-status--failed";

    case QUEUE_STATUS.PROCESSING:
      return "parsing-queue-status parsing-queue-status--processing";

    case QUEUE_STATUS.QUEUED:
    default:
      return "parsing-queue-status";
  }
}

function getEmailKey(item, index) {
  return (
    item?.emailId ||
    item?.email_id ||
    item?.id ||
    `queue-item-${index}`
  );
}

export default function ParsingQueue({
  items = [],
  visible = true,
}) {
  const queueItems = Array.isArray(items)
    ? items
    : [];

  if (
    !visible ||
    queueItems.length === 0
  ) {
    return null;
  }

  return (
    <section
      className="parsing-queue"
      aria-label="Parsing queue"
    >
      <header className="parsing-queue__header">
        <div>
          <h2>Parsing Queue</h2>

          <span>
            {queueItems.length} selected email
            {queueItems.length === 1
              ? ""
              : "s"}
          </span>
        </div>
      </header>

      <div className="parsing-queue__list">
        {queueItems.map(
          (item, index) => {
            const status =
              normalizeStatus(
                item?.status,
              );

            const emailKey =
              getEmailKey(
                item,
                index,
              );

            return (
              <article
                key={emailKey}
                className="parsing-queue-item"
              >
                <div className="parsing-queue-item__identity">
                  <strong
                    title={
                      item?.subject ||
                      "(No subject)"
                    }
                  >
                    {item?.subject ||
                      "(No subject)"}
                  </strong>

                  <span
                    title={
                      item?.sender ||
                      "Unknown sender"
                    }
                  >
                    {item?.sender ||
                      "Unknown sender"}
                  </span>
                </div>

                <div className="parsing-queue-item__state">
                  {status ===
                    QUEUE_STATUS.PROCESSING && (
                    <span
                      className="parsing-loading-indicator"
                      aria-label="Processing"
                    />
                  )}

                  <span
                    className={getQueueStatusClass(
                      status,
                    )}
                  >
                    {getQueueStatusLabel(
                      status,
                    )}
                  </span>
                </div>

                {item?.message && (
                  <p className="parsing-queue-item__message">
                    {String(item.message)}
                  </p>
                )}
              </article>
            );
          },
        )}
      </div>
    </section>
  );
}