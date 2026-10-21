import React, {
  useMemo,
} from "react";

import {
  FEATURE_DEFINITIONS,
  getFeatureDefinition,
} from "../types";

import FeatureValue from "./FeatureValue";


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function FeatureVector({
  featureVector = {},
  featureValues = [],
  status,
  loading = false,
  layout = "table",
}) {
  const features = useMemo(() => {
    // --------------------------------------------------------
    // If backend already supplied detailed feature values,
    // prefer those.
    // --------------------------------------------------------

    if (
      Array.isArray(
        featureValues,
      ) &&
      featureValues.length > 0
    ) {
      return [...featureValues].sort(
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
    }

    // --------------------------------------------------------
    // Otherwise build display values from the canonical
    // F1-F12 definitions and the feature vector.
    // --------------------------------------------------------

    return FEATURE_DEFINITIONS.map(
      (definition) => ({
        id: definition.id,
        name: definition.name,
        description:
          definition.description,
        source:
          definition.source,
        calculation:
          definition.calculation,
        dataType:
          definition.dataType,
        value:
          featureVector[
            definition.id
          ],
        status,
      }),
    );
  }, [
    featureVector,
    featureValues,
    status,
  ]);

  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {
    return (
      <section className="feature-vector">
        <div className="feature-vector__state">
          Loading feature vector…
        </div>
      </section>
    );
  }

  // ==========================================================
  // EMPTY
  // ==========================================================

  if (features.length === 0) {
    return (
      <section className="feature-vector">
        <div className="feature-vector__state">
          No feature values are available.
        </div>
      </section>
    );
  }

  // ==========================================================
  // GRID LAYOUT
  // ==========================================================

  if (layout === "grid") {
    return (
      <section className="feature-vector">
        <div className="feature-vector__grid">
          {features.map(
            (feature) => {
              const definition =
                getFeatureDefinition(
                  feature.id,
                );

              return (
                <FeatureValue
                  key={
                    feature.id
                  }
                  id={
                    feature.id
                  }
                  name={
                    feature.name ||
                    definition?.name
                  }
                  value={
                    feature.value
                  }
                  dataType={
                    feature.dataType ||
                    definition?.dataType
                  }
                  status={
                    feature.status ||
                    status
                  }
                />
              );
            },
          )}
        </div>
      </section>
    );
  }

  // ==========================================================
  // TABLE LAYOUT
  // ==========================================================

  return (
    <section
      className="feature-vector"
      aria-label="Feature vector"
    >
      <div className="feature-table-wrapper">
        <table className="feature-table feature-vector-table">
          <thead>
            <tr>
              <th scope="col">
                ID
              </th>

              <th scope="col">
                Feature Name
              </th>

              <th scope="col">
                Value
              </th>

              <th scope="col">
                Type
              </th>
            </tr>
          </thead>

          <tbody>
            {features.map(
              (feature) => {
                const definition =
                  getFeatureDefinition(
                    feature.id,
                  );

                const dataType =
                  feature.dataType ||
                  definition?.dataType;

                return (
                  <tr
                    key={
                      feature.id
                    }
                  >
                    <td>
                      <strong>
                        {feature.id}
                      </strong>
                    </td>

                    <td>
                      {feature.name ||
                        definition?.name ||
                        "—"}
                    </td>

                    <td>
                      <FeatureValue
                        id={
                          feature.id
                        }
                        name={
                          feature.name ||
                          definition?.name
                        }
                        value={
                          feature.value
                        }
                        dataType={
                          dataType
                        }
                        status={
                          feature.status ||
                          status
                        }
                        compact
                      />
                    </td>

                    <td>
                      <span className="feature-data-type">
                        {dataType ||
                          "—"}
                      </span>
                    </td>
                  </tr>
                );
              },
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}