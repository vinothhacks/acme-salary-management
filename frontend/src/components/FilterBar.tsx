export type Filters = {
  q: string;
  country: string;
  band: string;
  status: string;
};

export const EMPTY_FILTERS: Filters = { q: "", country: "", band: "", status: "" };

type Props = {
  value: Filters;
  onChange: (next: Filters) => void;
};

const COUNTRIES = ["US", "GB", "IN", "DE", "SG", "AE", "AU", "JP"];
const BANDS = ["IC1", "IC2", "IC3", "IC4", "IC5", "IC6", "M1", "M2", "M3"];

export default function FilterBar({ value, onChange }: Props) {
  return (
    <div className="filters">
      <label>
        Search
        <input
          value={value.q}
          onChange={(e) => onChange({ ...value, q: e.target.value })}
          placeholder="Name, code, or email"
        />
      </label>
      <label>
        Country
        <select value={value.country} onChange={(e) => onChange({ ...value, country: e.target.value })}>
          <option value="">All</option>
          {COUNTRIES.map((code) => (
            <option key={code}>{code}</option>
          ))}
        </select>
      </label>
      <label>
        Band
        <select value={value.band} onChange={(e) => onChange({ ...value, band: e.target.value })}>
          <option value="">All</option>
          {BANDS.map((band) => (
            <option key={band}>{band}</option>
          ))}
        </select>
      </label>
      <label>
        Status
        <select value={value.status} onChange={(e) => onChange({ ...value, status: e.target.value })}>
          <option value="">All</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </label>
    </div>
  );
}
