import { useState, useEffect } from "react";
import { Outlet, NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import {
  LayoutDashboard,
  CheckSquare,
  FolderKanban,
  Calendar,
  BarChart3,
  Settings,
  LogOut,
  Bell,
  Menu,
  X,
  ChevronLeft,
  Check,
  Shield,
  Sparkles,
  Activity,
  Zap,
  TreePine,
  Users,
} from "lucide-react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "./ui/dropdown-menu";
import { cn } from "../lib/utils";
import { formatDistanceToNow } from "date-fns";
import { tr } from "date-fns/locale";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/tasks", icon: CheckSquare, label: "Görevler" },
  { to: "/projects", icon: FolderKanban, label: "Projeler" },
  { to: "/calendar", icon: Calendar, label: "Takvim" },
  { to: "/jira-tools", icon: Sparkles, label: "Jira Araçları", gradient: "from-purple-500 to-pink-500" },
  { to: "/analysis", icon: Activity, label: "Analiz", gradient: "from-blue-500 to-cyan-500" },
  { to: "/product-tree", icon: TreePine, label: "Kapsam Ağacı", gradient: "from-emerald-500 to-teal-500" },
  { to: "/reports", icon: BarChart3, label: "Raporlar" },
  { to: "/settings", icon: Settings, label: "Ayarlar" },
];

// Admin-only nav item
const adminNavItem = { to: "/admin", icon: Shield, label: "Admin Panel", adminOnly: true };

const Layout = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [notifOpen, setNotifOpen] = useState(false);
  const [sseConnected, setSseConnected] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);

  // Check admin status
  useEffect(() => {
    const checkAdmin = async () => {
      if (!user?.name) return;
      try {
        const deviceId = user.device_id || localStorage.getItem('qa_device_id');
        const response = await api.get(`/admin/check?username=${encodeURIComponent(user.name)}&device_id=${encodeURIComponent(deviceId)}`);
        setIsAdmin(response.data.is_admin);
      } catch (error) {
        setIsAdmin(false);
      }
    };
    checkAdmin();
  }, [user?.name, user?.device_id]);

  // Debug: Log user info
  useEffect(() => {
    if (user) {
      console.log("=== USER INFO DEBUG ===");
      console.log("User object:", user);
      console.log("User role:", user.role);
      console.log("Is admin?", user.role === "admin");
      console.log("=======================");
    }
  }, [user]);

  useEffect(() => {
    fetchNotifications();
    
    // Establish SSE connection for real-time notifications
    if (user?.id) {
      // Use same base URL as api.js - localhost:8001 for localhost deployment
      const backendUrl = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_API_URL || "http://localhost:8001";
      const eventSource = new EventSource(
        `${backendUrl}/api/notifications/stream?user_id=${user.id}`
      );

      eventSource.onopen = () => {
        console.log("SSE connection established");
        setSseConnected(true);
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'connected') {
            console.log("SSE:", data.message);
          } else {
            // New notification received
            console.log("New notification received:", data);
            setNotifications(prev => [data, ...prev]);
            
            // Show toast notification (if you have toast)
            // toast.info(data.title, { description: data.message });
          }
        } catch (error) {
          console.error("Error parsing SSE message:", error);
        }
      };

      eventSource.onerror = (error) => {
        console.error("SSE error:", error);
        setSseConnected(false);
        eventSource.close();
      };

      return () => {
        eventSource.close();
        setSseConnected(false);
      };
    }
  }, [user?.id]);

  const fetchNotifications = async () => {
    try {
      const response = await api.get("/notifications");
      setNotifications(response.data);
    } catch (error) {
      console.error("Error fetching notifications:", error);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const markAsRead = async (notificationId) => {
    try {
      await api.put(`/notifications/${notificationId}/read`);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
    } catch (error) {
      console.error("Error marking notification as read:", error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.put("/notifications/read-all");
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (error) {
      console.error("Error marking all as read:", error);
    }
  };

  const getPageTitle = () => {
    const path = location.pathname;
    if (path === "/") return "Dashboard";
    const item = navItems.find(item => item.to === path);
    return item?.label || "QA Task Manager";
  };

  const getNotifTypeColor = (type) => {
    switch (type) {
      case "success": return "text-green-400";
      case "warning": return "text-orange-400";
      case "error": return "text-red-400";
      default: return "text-blue-400";
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden lg:flex flex-col border-r border-border bg-card transition-all duration-300",
          sidebarOpen ? "w-64" : "w-20"
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-border">
          {sidebarOpen && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-primary to-purple-600 flex items-center justify-center shadow-lg shadow-primary/20">
                <Zap className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="font-heading font-bold text-lg bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">QA Hub</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="hover:bg-secondary"
            data-testid="sidebar-toggle"
          >
            <ChevronLeft className={cn("w-5 h-5 transition-transform", !sidebarOpen && "rotate-180")} />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                )
              }
              data-testid={`nav-${item.label.toLowerCase()}`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="font-medium">{item.label}</span>}
            </NavLink>
          ))}
          
          {/* Admin-only: Ekip Takibi */}
          {isAdmin && (
            <NavLink
              to="/team-tracking"
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                  isActive
                    ? "bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-lg shadow-violet-500/20"
                    : "text-muted-foreground hover:text-foreground hover:bg-violet-500/10"
                )
              }
              data-testid="nav-team-tracking"
            >
              <Users className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="font-medium">Ekip Takibi</span>}
            </NavLink>
          )}
        </nav>

        {/* User Info */}
        <div className="p-4 border-t border-border">
          <div className={cn("flex items-center gap-3", !sidebarOpen && "justify-center")}>
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
              <span className="text-primary font-semibold">
                {user?.name?.charAt(0).toUpperCase()}
              </span>
            </div>
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{user?.name}</p>
                <p className="text-xs text-muted-foreground truncate">
                  {user?.role === "admin" ? "Admin" : user?.role === "manager" ? "Manager" : "QA Engineer"}
                </p>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transform transition-transform duration-300 lg:hidden",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <CheckSquare className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-heading font-bold text-lg">QA Manager</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileMenuOpen(false)}
            data-testid="mobile-menu-close"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>
        <nav className="py-4 px-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                )
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
          
          {/* Admin Panel - Only for admins */}
          {user?.role === "admin" && (
            <NavLink
              to={adminNavItem.to}
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200",
                  isActive
                    ? "bg-red-600 text-white"
                    : "text-muted-foreground hover:text-foreground hover:bg-red-50 dark:hover:bg-red-950"
                )
              }
            >
              <adminNavItem.icon className="w-5 h-5" />
              <span className="font-medium">{adminNavItem.label}</span>
            </NavLink>
          )}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-h-screen">
        {/* Header */}
        <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm flex items-center justify-between px-4 lg:px-6 sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setMobileMenuOpen(true)}
              data-testid="mobile-menu-open"
            >
              <Menu className="w-5 h-5" />
            </Button>
            <h1 className="font-heading text-xl font-bold">{getPageTitle()}</h1>
          </div>

          <div className="flex items-center gap-2">
            {/* Notifications */}
            <DropdownMenu open={notifOpen} onOpenChange={setNotifOpen}>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="relative" data-testid="notifications-btn">
                  <Bell className="w-5 h-5" />
                  {unreadCount > 0 && (
                    <Badge className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center text-xs bg-primary">
                      {unreadCount}
                    </Badge>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-80">
                <div className="flex items-center justify-between px-3 py-2 border-b border-border">
                  <span className="font-semibold">Bildirimler</span>
                  {unreadCount > 0 && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-xs h-7"
                      onClick={markAllAsRead}
                    >
                      <Check className="w-3 h-3 mr-1" />
                      Tümünü Okundu İşaretle
                    </Button>
                  )}
                </div>
                <div className="max-h-[300px] overflow-y-auto">
                  {notifications.length > 0 ? (
                    notifications.slice(0, 10).map((notif) => (
                      <DropdownMenuItem 
                        key={notif.id} 
                        className={cn(
                          "flex flex-col items-start p-3 cursor-pointer",
                          !notif.is_read && "bg-secondary/50"
                        )}
                        onClick={() => markAsRead(notif.id)}
                      >
                        <div className="flex items-start gap-2 w-full">
                          <div className={cn("w-2 h-2 rounded-full mt-1.5 shrink-0", 
                            notif.is_read ? "bg-muted" : "bg-primary"
                          )} />
                          <div className="flex-1 min-w-0">
                            <p className={cn(
                              "font-medium text-sm",
                              getNotifTypeColor(notif.type)
                            )}>
                              {notif.title}
                            </p>
                            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                              {notif.message}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {formatDistanceToNow(new Date(notif.created_at), { 
                                addSuffix: true, 
                                locale: tr 
                              })}
                            </p>
                          </div>
                        </div>
                      </DropdownMenuItem>
                    ))
                  ) : (
                    <div className="p-4 text-center text-muted-foreground text-sm">
                      Bildirim yok
                    </div>
                  )}
                </div>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="gap-2" data-testid="user-menu-btn">
                  <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                    <span className="text-primary font-semibold text-sm">
                      {user?.name?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="hidden sm:inline font-medium">{user?.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={logout} className="text-destructive" data-testid="logout-btn">
                  <LogOut className="w-4 h-4 mr-2" />
                  Çıkış Yap
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-4 lg:p-6 overflow-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
