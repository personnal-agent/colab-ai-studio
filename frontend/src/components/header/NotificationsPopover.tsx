import React from 'react';
import * as Popover from '@radix-ui/react-popover';
import { Bell, CheckCircle2, Clock } from 'lucide-react';

export interface NotificationItem {
  id: string; title: string; message: string; time?: string; read?: boolean;
}

interface NotificationsPopoverProps {
  notifications?: NotificationItem[];
}

export const NotificationsPopover: React.FC<NotificationsPopoverProps> = ({ notifications = [] }) => {
  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button type="button" aria-label="Centre de notifications" className="relative p-2 rounded-full border border-studio-border bg-white text-gray-600 hover:text-gray-900 hover:bg-studio-subtle transition-colors shadow-sm">
          <Bell className="w-4 h-4" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-indigo-600 text-[10px] font-bold text-white flex items-center justify-center">{unreadCount}</span>
          )}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content align="end" sideOffset={8} className="w-80 bg-white rounded-2xl shadow-dropdown border border-studio-border p-4 z-50 animate-in fade-in zoom-in-95">
          <div className="flex items-center justify-between border-b border-studio-border pb-2.5 mb-3">
            <h3 className="text-xs font-semibold text-gray-900">Notifications</h3>
            <span className="text-[11px] text-gray-500">{notifications.length} au total</span>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="py-6 text-center text-xs text-gray-400">Aucune nouvelle notification</div>
            ) : (
              notifications.map((n) => (
                <div key={n.id} className="p-2.5 rounded-xl bg-studio-canvas border border-studio-border/60 hover:border-studio-border transition-colors space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-900 flex items-center gap-1.5"><CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />{n.title}</span>
                    {n.time && <span className="text-[10px] text-gray-400 flex items-center gap-1"><Clock className="w-3 h-3" />{n.time}</span>}
                  </div>
                  <p className="text-[11px] text-gray-600 leading-relaxed">{n.message}</p>
                </div>
              ))
            )}
          </div>
          <Popover.Arrow className="fill-white" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
};
