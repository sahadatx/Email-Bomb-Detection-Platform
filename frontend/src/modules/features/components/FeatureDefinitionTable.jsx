import React, {
  useMemo,
} from "react";

import {
  FEATURE_DEFINITIONS,
  getFeatureDefinition,
} from "../types";


// ============================================================
// HELPERS
// ============================================================

function formatDataType(value) {
  if (!value) {
    return "—";
  }

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}


function formatSource(value) {
  if (!value) {
    return "—";
  }

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}


// ============================================================
// EMPTY STATE
// ============================================================

function EmptyState() {
  return (
    <div className="feature-definition-table__empty">
      No feature definitions are available.
    </div>
  );
}


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function FeatureDefinitionTable({
  definitions = FEATURE_DEFINITIONS,
}) {
  const orderedDefinitions =
    useMemo(() => {
      return [...definitions].sort(
        (left, right) => {
          const leftNumber =
            Number(
              String(left.id)
                .replace("F", ""),
            );

          const rightNumber =
            Number(
              String(right.id)
                .replace("F", ""),
            );

          return (
            leftNumber -
            rightNumber
          );
        },
      );
    }, [definitions]);

  // ----------------------------------------------------------
  // Empty
  // ----------------------------------------------------------

  if (
    orderedDefinitions.length === 0
  ) {
    return <EmptyState />;
  }

  // ==========================================================
  // TABLE
  // ==========================================================

  return (
    <div className="feature-table-wrapper">
      <table
        className="feature-table feature-definition-table"
      >
        <thead>
          <tr>
            <th scope="col">
              ID
            </th>

            <th scope="col">
              Feature
            </th>

            <th scope="col">
              Description
            </th>

            <th scope="col">
              Type
            </th>

            <th scope="col">
              Source
            </th>

            <th scope="col">
              Calculation
            </th>
          </tr>
        </thead>

        <tbody>
          {orderedDefinitions.map(
            (definition) => {
              const fallback =
                getFeatureDefinition(
                  definition.id,
                );

              const name =
                definition.name ||
                fallback?.name ||
                "—";

              const description =
                definition.description ||
                fallback?.description ||
                "—";

              const dataType =
                definition.dataType ||
                fallback?.dataType;

              const source =
                definition.source ||
                fallback?.source;

              const calculation =
                definition.calculation ||
                fallback?.calculation ||
                "—";

              return (
                <tr
                  key={
                    definition.id
                  }
                >
                  {/* ====================================== */}
                  {/* ID                                     */}
                  {/* ====================================== */}

                  <td>
                    <strong className="feature-definition-id">
                      {definition.id}
                    </strong>
                  </td>

                  {/* ====================================== */}
                  {/* FEATURE                                */}
                  {/* ====================================== */}

                  <td>
                    <strong>
                      {name}
                    </strong>
                  </td>

                  {/* ====================================== */}
                  {/* DESCRIPTION                            */}
                  {/* ====================================== */}

                  <td>
                    <span className="feature-definition-description">
                      {description}
                    </span>
                  </td>

                  {/* ====================================== */}
                  {/* DATA TYPE                              */}
                  {/* ====================================== */}

                  <td>
                    <span className="feature-data-type">
                      {formatDataType(
                        dataType,
                      )}
                    </span>
                  </td>

                  {/* ====================================== */}
                  {/* SOURCE                                 */}
                  {/* ====================================== */}

                  <td>
                    <span className="feature-definition-source">
                      {formatSource(
                        source,
                      )}
                    </span>
                  </td>

                  {/* ====================================== */}
                  {/* CALCULATION                            */}
                  {/* ====================================== */}

                  <td>
                    <span className="feature-definition-calculation">
                      {calculation}
                    </span>
                  </td>
                </tr>
              );
            },
          )}
        </tbody>
      </table>
    </div>
  );
}