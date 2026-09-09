import React from 'react';

export interface ColumnDef<T> {
  key: string;
  header: string;
  align?: 'left' | 'center' | 'right';
  width?: string;
  render?: (row: T, index: number) => React.ReactNode;
}

export interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  keyExtractor: (row: T, index: number) => string | number;
  isLoading?: boolean;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  className?: string;
  density?: 'compact' | 'normal';
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  isLoading = false,
  emptyMessage = 'No records found',
  onRowClick,
  className = '',
  density = 'compact',
}: DataTableProps<T>) {
  const paddingStyles = {
    compact: 'py-2 px-3 text-xs',
    normal: 'py-3 px-4 text-sm',
  };

  const alignStyles = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right font-mono tabular-nums',
  };

  return (
    <div className={`overflow-x-auto rounded-cs border border-slate-800 bg-slate-900 ${className}`}>
      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="border-b border-slate-800 bg-slate-950/60">
            {columns.map((col) => (
              <th
                key={col.key}
                style={{ width: col.width }}
                className={`text-[11px] font-mono uppercase tracking-wider text-slate-400 font-medium ${
                  paddingStyles[density]
                } ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/50">
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="text-center py-10 text-slate-400 text-xs font-mono">
                <div className="inline-flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                  <span>Loading portfolio telemetry...</span>
                </div>
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="text-center py-10 text-slate-500 text-xs font-mono">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, idx) => (
              <tr
                key={keyExtractor(row, idx)}
                onClick={() => onRowClick?.(row)}
                className={`transition-colors duration-100 ${
                  onRowClick ? 'cursor-pointer hover:bg-slate-800/50' : 'hover:bg-slate-800/25'
                }`}
              >
                {columns.map((col) => {
                  const align = col.align || 'left';
                  const cellContent = col.render
                    ? col.render(row, idx)
                    : (row as Record<string, unknown>)[col.key] != null
                    ? String((row as Record<string, unknown>)[col.key])
                    : '—';

                  return (
                    <td
                      key={col.key}
                      className={`${paddingStyles[density]} ${alignStyles[align]} text-slate-300`}
                    >
                      {cellContent}
                    </td>
                  );
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
