/**
 * Attachment List
 *
 * Displays normalized attachment metadata
 * extracted from the parsed MIME message.
 */

function formatSize(bytes) {
  if (
    bytes === null ||
    bytes === undefined ||
    bytes === ""
  ) {
    return "—";
  }

  const size = Number(bytes);

  if (!Number.isFinite(size) || size < 0) {
    return "—";
  }

  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  if (size < 1024 * 1024 * 1024) {
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  return `${(
    size /
    (1024 * 1024 * 1024)
  ).toFixed(1)} GB`;
}

function getAttachmentName(
  attachment,
  index,
) {
  const filename = attachment?.filename;

  if (
    filename !== null &&
    filename !== undefined &&
    String(filename).trim() !== ""
  ) {
    return String(filename);
  }

  return `Attachment ${index}`;
}

function getAttachmentContentType(
  attachment,
) {
  return (
    attachment?.content_type ||
    attachment?.contentType ||
    "—"
  );
}

function getAttachmentDisposition(
  attachment,
) {
  return (
    attachment?.content_disposition ||
    attachment?.contentDisposition ||
    "—"
  );
}

function getAttachmentContentId(
  attachment,
) {
  return (
    attachment?.content_id ||
    attachment?.contentId ||
    "—"
  );
}

export default function AttachmentList({
  attachments = [],
}) {
  const items = Array.isArray(attachments)
    ? attachments
    : [];

  return (
    <section className="parsing-detail-card">
      <header className="parsing-detail-card__header">
        <div>
          <span className="parsing-detail-card__eyebrow">
            FILE ANALYSIS
          </span>

          <h2>Attachments</h2>

          <p>
            Attachment metadata extracted from the
            parsed MIME message.
          </p>
        </div>

        <span className="parsing-detail-card__count">
          {items.length} attachment
          {items.length === 1 ? "" : "s"}
        </span>
      </header>

      {items.length === 0 ? (
        <div className="parsing-empty-state">
          <strong>
            No attachments detected.
          </strong>

          <span>
            This email does not contain parsed
            attachment metadata.
          </span>
        </div>
      ) : (
        <div className="parsing-attachment-table-wrapper">
          <table className="parsing-attachment-table">
            <thead>
              <tr>
                <th scope="col">
                  Filename
                </th>

                <th scope="col">
                  Content Type
                </th>

                <th scope="col">
                  Disposition
                </th>

                <th scope="col">
                  Size
                </th>

                <th scope="col">
                  Content ID
                </th>
              </tr>
            </thead>

            <tbody>
              {items.map(
                (attachment, index) => {
                  const name =
                    getAttachmentName(
                      attachment,
                      index + 1,
                    );

                  return (
                    <tr
                      key={`${name}-${index}`}
                    >
                      <td>
                        <strong>
                          {name}
                        </strong>
                      </td>

                      <td>
                        <code>
                          {getAttachmentContentType(
                            attachment,
                          )}
                        </code>
                      </td>

                      <td>
                        {getAttachmentDisposition(
                          attachment,
                        )}
                      </td>

                      <td>
                        {formatSize(
                          attachment?.size,
                        )}
                      </td>

                      <td>
                        <code>
                          {getAttachmentContentId(
                            attachment,
                          )}
                        </code>
                      </td>
                    </tr>
                  );
                },
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}