import * as Popover from '@radix-ui/react-popover';
import { Bell, CheckCircle2, Clock } from 'lucide-react';

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  time: string;
  type?: 'success' | 'info' | 'error';
}

interface NotificationsPopoverProps {
  notifications?: NotificationItem[];
}

export function NotificationsPopover({ notifications = [] }: NotificationsPopoverProps) {
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-label="Notifications"
          className="p-2 rounded-slot text-gray-600 hover:text-gray-900 hover:bg-studio-subtle transition-colors relative"
        >
          <Bell className="w-5 h-5" />
          {notifications.length > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-indigo-600 rounded-full" />
          )}
        </button>
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={8}
          className="w-80 bg-white rounded-menu shadow-dropdown border border-studio-border p-4 z-50 animate-in fade-in zoom-in-95"
        >
          <div className="flex items-center justify-between pb-2 border-b border-studio-border mb-3">
            <span className="text-sm font-semibold text-gray-900">Notifications</span>
            <span className="text-xs text-gray-400">{notifications.length} nouvelles</span>
          </div>

          {notifications.length === 0 ? (
            <div className="py-6 text-center text-xs text-gray-400 flex flex-col items-center gap-1.5">
              <CheckCircle2 className="w-6 h-6 stroke-gray-300" />
              <span>Aucune notification récente</span>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-60 overflow-y-auto">
              {notifications.map((n) => (
                <div key={n.id} className="p-2 rounded-slot bg-studio-canvas text-xs space-y-0.5">
                  <div className="font-medium text-gray-800">{n.title}</div>
                  <div className="text-gray-500">{n.message}</div>
                  <div className="text-[10px] text-gray-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{n.time}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
