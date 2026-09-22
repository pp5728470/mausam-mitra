"use client";

import { BrandMark } from "@/components/shared/brand-mark";
import { SidebarFooter } from "@/components/layout/sidebar-footer";
import { SidebarNav } from "@/components/layout/sidebar-nav";
import { useSidebar } from "@/hooks/use-sidebar";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

export function MobileSidebar() {
  const { mobileOpen, setMobileOpen } = useSidebar();

  return (
    <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
      <SheetContent
        side="left"
        showCloseButton
        className="w-[18.5rem] gap-0 bg-sidebar p-0 sm:max-w-[18.5rem]"
      >
        <SheetHeader className="border-b border-sidebar-border">
          <SheetTitle className="sr-only">Command navigation</SheetTitle>
          <SheetDescription className="sr-only">
            Navigate Mausam Mitra command modules
          </SheetDescription>
          <BrandMark href="/overview" />
        </SheetHeader>
        <div className="flex min-h-0 flex-1 flex-col py-3">
          <SidebarNav forceExpanded onNavigate={() => setMobileOpen(false)} />
          <SidebarFooter />
        </div>
      </SheetContent>
    </Sheet>
  );
}
