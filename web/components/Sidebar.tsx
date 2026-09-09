"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Search, FolderSearch, FileText, Bell, Settings, HelpCircle } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/investigations", label: "Investigations", icon: Search },
  { href: "/evidence", label: "Evidence", icon: FolderSearch },
  { href: "/briefs", label: "Briefs", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-zinc-200 bg-white">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white font-bold">
          D
        </div>
        <span className="text-lg font-semibold text-zinc-900">Dailies</span>
      </div>

      <nav className="flex-1 px-3 py-2">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`mb-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-brand-50 text-brand-700"
                  : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900"
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}

        {
        
        }
        <div
          className="mb-1 flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-zinc-300"
          title="Not built yet -- no backing data model"
        >
          <Bell size={18} />
          Alerts
        </div>
      </nav>

      <div className="border-t border-zinc-200 px-3 py-3">
        <button className="mb-1 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-50">
          <Settings size={18} />
          Settings
        </button>
        <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-50">
          <HelpCircle size={18} />
          Help
        </button>
      </div>

      <div className="flex items-center gap-2 border-t border-zinc-200 px-4 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-200 text-xs font-semibold text-zinc-600">
          SS
        </div>
        <div className="text-xs">
          <div className="font-medium text-zinc-900">Studio Demo</div>
          <div className="text-zinc-500">Viewer</div>
        </div>
      </div>
    </aside>
  );
}
