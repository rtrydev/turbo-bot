import {
  Check,
  ChevronLeft,
  ChevronRight,
  Info,
  LayoutGrid,
  Library,
  Link2,
  List,
  LoaderCircle,
  Music,
  Pause,
  Play,
  Plus,
  Repeat,
  Search,
  Shuffle,
  SkipForward,
  Trash2,
  TriangleAlert,
  Wifi,
  X,
  Zap,
  type LucideIcon,
} from 'lucide-react';

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

const ICONS: Record<IconName, LucideIcon> = {
  bolt: Zap,
  play: Play,
  pause: Pause,
  skip: SkipForward,
  repeat: Repeat,
  shuffle: Shuffle,
  trash: Trash2,
  plus: Plus,
  search: Search,
  music: Music,
  grid: LayoutGrid,
  list: List,
  library: Library,
  check: Check,
  x: X,
  alert: TriangleAlert,
  info: Info,
  'chevron-left': ChevronLeft,
  'chevron-right': ChevronRight,
  link: Link2,
  loader: LoaderCircle,
  wifi: Wifi,
};

export function Icon({ name, className }: { name: IconName; className?: string }) {
  const Cmp = ICONS[name];
  return <Cmp className={className} strokeWidth={1.8} aria-hidden="true" />;
}
