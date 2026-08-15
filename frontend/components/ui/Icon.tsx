export type IconName =
  | 'bolt'
  | 'play'
  | 'pause'
  | 'skip'
  | 'repeat'
  | 'shuffle'
  | 'trash'
  | 'plus'
  | 'search'
  | 'music'
  | 'grid'
  | 'list'
  | 'library'
  | 'check'
  | 'x'
  | 'alert'
  | 'info'
  | 'chevron-left'
  | 'chevron-right'
  | 'link'
  | 'loader'
  | 'wifi';

interface IconDef {
  d: string[];
  fill?: boolean;
}

const ICONS: Record<IconName, IconDef> = {
  bolt: { d: ['M13 2 3 14h7l-1 8 10-12h-7l1-8z'], fill: true },
  play: { d: ['M8 5v14l11-7z'], fill: true },
  pause: { d: ['M6 4h4v16H6z', 'M14 4h4v16h-4z'], fill: true },
  skip: { d: ['M5 4l10 8-10 8V4z', 'M16 4h2v16h-2z'], fill: true },
  repeat: { d: ['M17 2l4 4-4 4', 'M3 11v-1a4 4 0 014-4h14', 'M7 22l-4-4 4-4', 'M21 13v1a4 4 0 01-4 4H3'] },
  shuffle: {
    d: [
      'M2 18h1.4c1.3 0 2.5-.6 3.3-1.7l6.1-8.6c.8-1.1 2-1.7 3.3-1.7H22',
      'm18 2 4 4-4 4',
      'M2 6h1.9c1.5 0 2.9.9 3.6 2.2',
      'M22 18h-5.9c-1.3 0-2.5-.6-3.3-1.7l-.5-.7',
      'm18 14 4 4-4 4',
    ],
  },
  trash: { d: ['M3 6h18', 'M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6', 'M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2', 'M10 11v6', 'M14 11v6'] },
  plus: { d: ['M12 5v14', 'M5 12h14'] },
  search: { d: ['M11 4a7 7 0 100 14 7 7 0 000-14z', 'M21 21l-4.35-4.35'] },
  music: { d: ['M9 18V5l12-2v13', 'M6 19a3 3 0 106 0 3 3 0 00-6 0z', 'M18 17a3 3 0 106 0 3 3 0 00-6 0z'] },
  grid: { d: ['M3 3h7v7H3z', 'M14 3h7v7h-7z', 'M14 14h7v7h-7z', 'M3 14h7v7H3z'] },
  list: { d: ['M8 6h13', 'M8 12h13', 'M8 18h13', 'M3.5 6h.01', 'M3.5 12h.01', 'M3.5 18h.01'] },
  library: { d: ['M4 5v14', 'M9 5v14', 'M14 6l4 13'] },
  check: { d: ['M20 6L9 17l-5-5'] },
  x: { d: ['M18 6L6 18', 'M6 6l12 12'] },
  alert: { d: ['M10.29 3.86 1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z', 'M12 9v4', 'M12 17h.01'] },
  info: { d: ['M12 3a9 9 0 100 18 9 9 0 000-18z', 'M12 16v-4', 'M12 8h.01'] },
  'chevron-left': { d: ['M15 18l-6-6 6-6'] },
  'chevron-right': { d: ['M9 18l6-6-6-6'] },
  link: {
    d: [
      'M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71',
      'M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71',
    ],
  },
  loader: { d: ['M21 12a9 9 0 11-6.22-8.56'] },
  wifi: { d: ['M5 12.55a11 11 0 0114.08 0', 'M8.53 16.11a6 6 0 016.95 0', 'M12 20h.01'] },
};

export function Icon({ name, className }: { name: IconName; className?: string }) {
  const def = ICONS[name];
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill={def.fill ? 'currentColor' : 'none'}
      stroke={def.fill ? 'none' : 'currentColor'}
      strokeWidth={def.fill ? undefined : 1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {def.d.map((d, i) => (
        <path key={i} d={d} />
      ))}
    </svg>
  );
}
