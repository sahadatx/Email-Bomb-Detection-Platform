
import { useCallback, useMemo } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Shuffle,
} from "lucide-react";

const SPLITS = [
  {
    key: "training_percentage",
    label: "Training",
    description: "Used to train the machine learning model.",
    color: "train",
    fallback: 70,
  },
  {
    key: "validation_percentage",
    label: "Validation",
    description: "Used for model tuning and selection.",
    color: "validation",
    fallback: 15,
  },
  {
    key: "testing_percentage",
    label: "Testing",
    description: "Used for final model evaluation.",
    color: "test",
    fallback: 15,
  },
];

const DEFAULTS = {
  training_percentage: 70,
  validation_percentage: 15,
  testing_percentage: 15,
  random_seed: 42,
  stratified: true,
};

function toNumber(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function normalizeConfiguration(value = {}) {
  return {
    training_percentage:
      value.training_percentage ??
      value.train_percent ??
      DEFAULTS.training_percentage,

    validation_percentage:
      value.validation_percentage ??
      value.validation_percent ??
      DEFAULTS.validation_percentage,

    testing_percentage:
      value.testing_percentage ??
      value.test_percent ??
      DEFAULTS.testing_percentage,

    random_seed:
      value.random_seed ??
      value.randomSeed ??
      DEFAULTS.random_seed,

    stratified:
      typeof value.stratified === "boolean"
        ? value.stratified
        : DEFAULTS.stratified,
  };
}

function validateConfiguration(configuration) {
  const percentages = SPLITS.map((split) =>
    toNumber(configuration[split.key])
  );

  if (percentages.some((value) => value === null)) {
    return {
      valid: false,
      total: null,
      message: "Enter all three split percentages.",
    };
  }

  if (
    percentages.some(
      (value) =>
        !Number.isInteger(value) ||
        value < 0 ||
        value > 100
    )
  ) {
    return {
      valid: false,
      total: percentages.reduce(
        (sum, value) => sum + (value ?? 0),
        0
      ),
      message:
        "Percentages must be whole numbers between 0 and 100.",
    };
  }

  const total = percentages.reduce(
    (sum, value) => sum + value,
    0
  );

  if (total !== 100) {
    return {
      valid: false,
      total,
      message: "Split percentages must total exactly 100%.",
    };
  }

  const seed = toNumber(configuration.random_seed);

  if (
    seed === null ||
    !Number.isInteger(seed) ||
    seed < 0
  ) {
    return {
      valid: false,
      total,
      message: "Random seed must be a non-negative integer.",
    };
  }

  return {
    valid: true,
    total,
    message: "",
  };
}

export default function DatasetSplitConfiguration({
  value,
  onChange,
  disabled = false,
  className = "",
}) {
  const configuration = useMemo(
    () => normalizeConfiguration(value),
    [value]
  );

  const validation = useMemo(
    () => validateConfiguration(configuration),
    [configuration]
  );

  const updateField = useCallback(
    (field, nextValue) => {
      onChange?.({
        ...configuration,
        [field]: nextValue,
      });
    },
    [configuration, onChange]
  );

  const handlePercentageChange = useCallback(
    (field, rawValue) => {
      updateField(
        field,
        rawValue === "" ? "" : Number(rawValue)
      );
    },
    [updateField]
  );

  const handleSeedChange = useCallback(
    (event) => {
      const rawValue = event.target.value;

      updateField(
        "random_seed",
        rawValue === "" ? "" : Number(rawValue)
      );
    },
    [updateField]
  );

  const handleStratifiedChange = useCallback(
    (event) => {
      updateField("stratified", event.target.checked);
    },
    [updateField]
  );

  return (
    <section
      className={`dataset-split-configuration ${className}`.trim()}
      aria-labelledby="dataset-split-title"
    >
      <div className="dataset-split-configuration__header">
        <div>
          <h3 id="dataset-split-title">
            Split Configuration
          </h3>
          <p>
            Define how dataset samples will be divided into
            training, validation, and testing sets.
          </p>
        </div>

        <span
          className={`dataset-split-total ${
            validation.valid
              ? "dataset-split-total--valid"
              : "dataset-split-total--invalid"
          }`}
          aria-live="polite"
        >
          {validation.total === null
            ? "—"
            : `${validation.total}%`}{" "}
          / 100%
        </span>
      </div>

      <div className="dataset-split-configuration__fields">
        {SPLITS.map((split) => (
          <div
            className={`dataset-split-field dataset-split-field--${split.color}`}
            key={split.key}
          >
            <div className="dataset-split-field__heading">
              <label htmlFor={`split-${split.key}`}>
                {split.label}
              </label>
              <span className="dataset-split-field__unit">
                %
              </span>
            </div>

            <input
              id={`split-${split.key}`}
              className="dataset-split-field__input"
              type="number"
              min="0"
              max="100"
              step="1"
              value={configuration[split.key] ?? ""}
              onChange={(event) =>
                handlePercentageChange(
                  split.key,
                  event.target.value
                )
              }
              disabled={disabled}
              aria-label={`${split.label} percentage`}
              aria-invalid={!validation.valid}
            />

            <p>{split.description}</p>
          </div>
        ))}
      </div>

      <div className="dataset-split-configuration__visual">
        <div
          className="dataset-split-configuration__bar"
          role="img"
          aria-label={
            validation.total === null
              ? "Split distribution is incomplete"
              : `Split distribution total: ${validation.total}%`
          }
        >
          {SPLITS.map((split) => {
            const percentage = toNumber(
              configuration[split.key]
            );

            if (percentage === null || percentage <= 0) {
              return null;
            }

            return (
              <div
                key={split.key}
                className={`dataset-split-configuration__segment dataset-split-configuration__segment--${split.color}`}
                style={{
                  width: `${Math.min(percentage, 100)}%`,
                }}
                title={`${split.label}: ${percentage}%`}
              />
            );
          })}
        </div>

        <div className="dataset-split-configuration__legend">
          {SPLITS.map((split) => (
            <span key={split.key}>
              <i
                className={`dataset-split-configuration__dot dataset-split-configuration__dot--${split.color}`}
              />
              {split.label}:{" "}
              {configuration[split.key] ?? "—"}%
            </span>
          ))}
        </div>
      </div>

      <div className="dataset-split-configuration__seed">
        <div className="dataset-split-configuration__seed-heading">
          <Shuffle size={17} />
          <div>
            <label htmlFor="dataset-random-seed">
              Random Seed
            </label>
            <p>
              Use the same seed to reproduce a split
              configuration.
            </p>
          </div>
        </div>

        <input
          id="dataset-random-seed"
          type="number"
          min="0"
          step="1"
          value={configuration.random_seed ?? ""}
          onChange={handleSeedChange}
          disabled={disabled}
        />
      </div>

      <label className="dataset-split-configuration__stratified">
        <input
          type="checkbox"
          checked={configuration.stratified}
          onChange={handleStratifiedChange}
          disabled={disabled}
        />
        <span>
          <strong>Stratified Split</strong>
          <small>
            Preserve the class distribution across the
            splits, when supported by the dataset.
          </small>
        </span>
      </label>

      <div
        className={`dataset-split-configuration__validation ${
          validation.valid
            ? "dataset-split-configuration__validation--valid"
            : "dataset-split-configuration__validation--invalid"
        }`}
        role="status"
        aria-live="polite"
      >
        {validation.valid ? (
          <>
            <CheckCircle2 size={17} />
            <span>Split percentages total 100%.</span>
          </>
        ) : (
          <>
            <AlertCircle size={17} />
            <span>{validation.message}</span>
          </>
        )}
      </div>
    </section>
  );
}