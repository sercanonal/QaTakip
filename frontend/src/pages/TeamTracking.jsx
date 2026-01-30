import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { toast } from "sonner";
import { 
  Search,
  Loader2,
  Users,
  AlertCircle,
  Clock,
  ListTodo,
  ShieldAlert,
  User,
} from "lucide-react";

const STATUS_LABELS = {
  'in_progress': 'Devam Ediyor',
  'backlog': 'Backlog',
  'today_planned': 'Bugün Planlandı',
};

const STATUS_COLORS = {
  'in_progress': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'backlog': 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
  'today_planned': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
};

const PRIORITY_LABELS = {
  'critical': 'Kritik',
  'high': 'Yüksek',
  'medium': 'Orta',
  'low': 'Düşük',
};

const PRIORITY_COLORS = {
  'critical': 'bg-red-500/20 text-red-400 border-red-500/30',
  'high': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  'medium': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  'low': 'bg-green-500/20 text-green-400 border-green-500/30',
};

const TeamTracking = () => {
  const { user } = useAuth();
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [searchUsername, setSearchUsername] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [allUsers, setAllUsers] = useState([]);

  // Check admin status on mount
  useEffect(() => {
    checkAdminStatus();
  }, [user]);

  const checkAdminStatus = async () => {
    if (!user?.name || !user?.device_id) {
      setLoading(false);
      return;
    }

    try {
      const deviceId = user.device_id || localStorage.getItem('qa_device_id');
      const response = await api.get(`/admin/check?username=${encodeURIComponent(user.name)}&device_id=${encodeURIComponent(deviceId)}`);
      setIsAdmin(response.data.is_admin);
      
      if (response.data.is_admin) {
        loadAllUsers();
      }
    } catch (error) {
      console.error("Admin check error:", error);
      setIsAdmin(false);
    } finally {
      setLoading(false);
    }
  };

  const loadAllUsers = async () => {
    try {
      const deviceId = user.device_id || localStorage.getItem('qa_device_id');
      const response = await api.get(`/admin/all-users?requester_username=${encodeURIComponent(user.name)}&requester_device_id=${encodeURIComponent(deviceId)}`);
      setAllUsers(response.data.users || []);
    } catch (error) {
      console.error("Error loading users:", error);
    }
  };

  const handleSearch = async () => {
    if (!searchUsername.trim()) {
      toast.error("Kullanıcı adı girin");
      return;
    }

    setSearching(true);
    setSearchResult(null);

    try {
      const deviceId = user.device_id || localStorage.getItem('qa_device_id');
      const response = await api.get(
        `/admin/team-tasks?search_username=${encodeURIComponent(searchUsername)}&requester_username=${encodeURIComponent(user.name)}&requester_device_id=${encodeURIComponent(deviceId)}`
      );
      setSearchResult(response.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Bu özelliğe erişim yetkiniz yok");
        setIsAdmin(false);
      } else {
        toast.error("Arama yapılamadı");
      }
    } finally {
      setSearching(false);
    }
  };

  const handleUserClick = (username) => {
    setSearchUsername(username);
    // Auto search
    setTimeout(() => {
      document.getElementById('search-btn')?.click();
    }, 100);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  // Not admin - show access denied
  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
          <ShieldAlert className="w-10 h-10 text-red-500" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Erişim Engellendi</h2>
        <p className="text-muted-foreground max-w-md">
          Bu sayfaya erişim yetkiniz bulunmuyor. Admin yetkisi için yöneticinize başvurun.
        </p>
        <p className="text-xs text-muted-foreground mt-4">
          Device ID'nizi Ayarlar sayfasında bulabilirsiniz.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <h2 className="font-heading text-2xl font-bold flex items-center gap-2">
          <Users className="w-6 h-6 text-primary" />
          Ekip Takibi
        </h2>
        <p className="text-muted-foreground">
          Ekip üyelerinin görevlerini görüntüleyin (Backlog ve Devam Eden)
        </p>
      </div>

      {/* Search Card */}
      <Card className="border-border/50 bg-card">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="w-5 h-5 text-primary" />
            Kullanıcı Ara
          </CardTitle>
          <CardDescription>
            Intertech kullanıcı adı ile arama yapın
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Kullanıcı adı girin (örn: SERCANO)"
              value={searchUsername}
              onChange={(e) => setSearchUsername(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
              data-testid="search-username-input"
            />
            <Button 
              id="search-btn"
              onClick={handleSearch} 
              disabled={searching}
              data-testid="search-btn"
            >
              {searching ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Ara
                </>
              )}
            </Button>
          </div>

          {/* Quick user list */}
          {allUsers.length > 0 && (
            <div className="mt-4">
              <p className="text-xs text-muted-foreground mb-2">Hızlı seçim:</p>
              <div className="flex flex-wrap gap-2">
                {allUsers.slice(0, 10).map((u) => (
                  <Button
                    key={u.id}
                    variant="outline"
                    size="sm"
                    onClick={() => handleUserClick(u.name)}
                    className="h-7 text-xs"
                  >
                    <User className="w-3 h-3 mr-1" />
                    {u.name}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Search Results */}
      {searchResult && (
        <Card className="border-border/50 bg-card">
          <CardHeader>
            {searchResult.found ? (
              <>
                <CardTitle className="text-lg flex items-center gap-2">
                  <User className="w-5 h-5 text-primary" />
                  {searchResult.user?.name}
                </CardTitle>
                <CardDescription>
                  <div className="flex gap-4 mt-2">
                    <Badge variant="outline" className="bg-blue-500/10 text-blue-400">
                      <Clock className="w-3 h-3 mr-1" />
                      Devam Eden: {searchResult.summary?.in_progress || 0}
                    </Badge>
                    <Badge variant="outline" className="bg-zinc-500/10 text-zinc-400">
                      <ListTodo className="w-3 h-3 mr-1" />
                      Backlog: {searchResult.summary?.backlog || 0}
                    </Badge>
                  </div>
                </CardDescription>
              </>
            ) : (
              <CardTitle className="text-lg flex items-center gap-2 text-amber-500">
                <AlertCircle className="w-5 h-5" />
                {searchResult.message}
              </CardTitle>
            )}
          </CardHeader>
          
          {searchResult.found && searchResult.tasks?.length > 0 && (
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Görev</TableHead>
                    <TableHead>Durum</TableHead>
                    <TableHead>Öncelik</TableHead>
                    <TableHead>Bitiş Tarihi</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {searchResult.tasks.map((task) => (
                    <TableRow key={task.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{task.title}</p>
                          {task.description && (
                            <p className="text-xs text-muted-foreground line-clamp-1">
                              {task.description}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant="outline" 
                          className={STATUS_COLORS[task.status] || ''}
                        >
                          {STATUS_LABELS[task.status] || task.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant="outline" 
                          className={PRIORITY_COLORS[task.priority] || ''}
                        >
                          {PRIORITY_LABELS[task.priority] || task.priority}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {task.due_date ? new Date(task.due_date).toLocaleDateString('tr-TR') : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          )}
          
          {searchResult.found && searchResult.tasks?.length === 0 && (
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <ListTodo className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Bu kullanıcının aktif görevi bulunmuyor</p>
              </div>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
};

export default TeamTracking;
