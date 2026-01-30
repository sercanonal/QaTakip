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
  Lock,
  ExternalLink,
  Key,
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
  const [adminKey, setAdminKey] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [searchUsername, setSearchUsername] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);

  // Check if admin key is saved in session
  useEffect(() => {
    const savedKey = sessionStorage.getItem('admin_key');
    if (savedKey) {
      setAdminKey(savedKey);
      verifyKey(savedKey);
    }
  }, []);

  const verifyKey = async (key) => {
    setVerifying(true);
    try {
      const response = await api.post('/admin/verify-key', { admin_key: key });
      if (response.data.valid) {
        setIsAuthenticated(true);
        sessionStorage.setItem('admin_key', key);
        toast.success("Admin girişi başarılı!");
      } else {
        setIsAuthenticated(false);
        sessionStorage.removeItem('admin_key');
        toast.error("Geçersiz admin anahtarı");
      }
    } catch (error) {
      setIsAuthenticated(false);
      toast.error("Doğrulama başarısız");
    } finally {
      setVerifying(false);
    }
  };

  const handleKeySubmit = (e) => {
    e.preventDefault();
    if (!adminKey.trim()) {
      toast.error("Admin anahtarı girin");
      return;
    }
    verifyKey(adminKey);
  };

  const handleSearch = async () => {
    if (!searchUsername.trim()) {
      toast.error("Kullanıcı adı girin");
      return;
    }

    setSearching(true);
    setSearchResult(null);

    try {
      const response = await api.get(
        `/admin/team-tasks?search_username=${encodeURIComponent(searchUsername)}&admin_key=${encodeURIComponent(adminKey)}`
      );
      setSearchResult(response.data);
      
      if (response.data.found) {
        toast.success(`${response.data.summary?.total || 0} görev bulundu`);
      }
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Erişim reddedildi");
        setIsAuthenticated(false);
        sessionStorage.removeItem('admin_key');
      } else {
        toast.error("Arama yapılamadı");
      }
    } finally {
      setSearching(false);
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setAdminKey("");
    setSearchResult(null);
    sessionStorage.removeItem('admin_key');
    toast.info("Çıkış yapıldı");
  };

  // Not authenticated - show login form
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="w-full max-w-md border-border/50 bg-card">
          <CardHeader className="text-center">
            <div className="w-16 h-16 rounded-full bg-violet-500/10 flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-violet-500" />
            </div>
            <CardTitle className="text-xl">Ekip Takibi</CardTitle>
            <CardDescription>
              Bu özelliğe erişmek için admin anahtarı gereklidir.
              <br />
              <span className="text-xs text-muted-foreground">Anahtarı yöneticinizden alabilirsiniz.</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleKeySubmit} className="space-y-4">
              <div className="relative">
                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  type="password"
                  placeholder="Admin anahtarını girin..."
                  value={adminKey}
                  onChange={(e) => setAdminKey(e.target.value)}
                  className="pl-10"
                  data-testid="admin-key-input"
                />
              </div>
              <Button 
                type="submit" 
                className="w-full"
                disabled={verifying}
                data-testid="admin-login-btn"
              >
                {verifying ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Lock className="w-4 h-4 mr-2" />
                )}
                Giriş Yap
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-2xl font-bold flex items-center gap-2">
            <Users className="w-6 h-6 text-violet-500" />
            Ekip Takibi
          </h2>
          <p className="text-muted-foreground">
            Jira'dan ekip üyelerinin görevlerini görüntüleyin
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleLogout}>
          Çıkış
        </Button>
      </div>

      {/* Search Card */}
      <Card className="border-border/50 bg-card">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="w-5 h-5 text-violet-500" />
            Jira Kullanıcı Ara
          </CardTitle>
          <CardDescription>
            Jira kullanıcı adı ile arama yapın (Intertech AD kullanıcı adı)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Kullanıcı adı girin (örn: sercano, burakg)"
              value={searchUsername}
              onChange={(e) => setSearchUsername(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
              data-testid="search-username-input"
            />
            <Button 
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
        </CardContent>
      </Card>

      {/* Search Results */}
      {searchResult && (
        <Card className="border-border/50 bg-card">
          <CardHeader>
            {searchResult.found ? (
              <>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Users className="w-5 h-5 text-violet-500" />
                  {searchResult.user?.name}
                  <Badge variant="outline" className="ml-2 bg-violet-500/10 text-violet-400">
                    Jira
                  </Badge>
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
                    <TableHead>Jira Durumu</TableHead>
                    <TableHead>Öncelik</TableHead>
                    <TableHead>Bitiş Tarihi</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {searchResult.tasks.map((task) => (
                    <TableRow key={task.id}>
                      <TableCell>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium">{task.title}</p>
                            {task.jira_key && (
                              <a 
                                href={`https://jira.intertech.com.tr/browse/${task.jira_key}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-violet-500 hover:text-violet-400"
                              >
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>
                          {task.description && (
                            <p className="text-xs text-muted-foreground line-clamp-1 mt-1">
                              {task.description}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={STATUS_COLORS[task.status] || ''}>
                          {task.jira_status || STATUS_LABELS[task.status] || task.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={PRIORITY_COLORS[task.priority] || ''}>
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
                <p>Bu kullanıcının açık görevi bulunmuyor</p>
              </div>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
};

export default TeamTracking;
