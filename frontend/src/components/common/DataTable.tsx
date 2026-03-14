interface Props {
  data: Record<string, unknown>[];
  maxRows?: number;
}

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return "-";
  if (typeof val === "number") {
    return val.toLocaleString("ko-KR", { maximumFractionDigits: 2 });
  }
  const s = String(val);
  return s.length > 200 ? s.slice(0, 197) + "..." : s;
}

export default function DataTable({ data, maxRows = 100 }: Props) {
  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);
  const rows = data.slice(0, maxRows);

  return (
    <div className="overflow-x-auto my-2">
      <table className="min-w-full text-sm border border-gray-200">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="bg-gray-50 px-3 py-2 text-left font-medium border-b"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td key={col} className="px-3 py-2 border-b border-gray-100">
                  {formatValue(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > maxRows && (
        <p className="text-xs text-gray-500 mt-1">
          {data.length}건 중 {maxRows}건 표시
        </p>
      )}
    </div>
  );
}
