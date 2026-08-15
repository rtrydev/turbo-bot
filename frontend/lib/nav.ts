import type { IconName } from '@/components/ui/Icon';

export interface NavItem {
  label: string;
  href: string;
  icon: IconName;
}

export const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/', icon: 'grid' },
  { label: 'Queue', href: '/queue', icon: 'list' },
  { label: 'Songs', href: '/songs', icon: 'library' },
];
