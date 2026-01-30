import { useState } from "react";
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
  UserCheck,
} from "lucide-react";

const STATUS_COLORS = {
  'in_progress': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'backlog': 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
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
  const [inputVal, setInputVal] = useState("");
  const [isAuth, setIsAuth] = useState(false);
  const [checking, setChecking] = useState(false);
  const [storedVal, setStoredVal] = useState("");
  const [searchUsername, setSearchUsername] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [qaTeam, setQaTeam] = useState([]);
  const [loadingTeam, setLoadingTeam] = useState(false);
  const [showTeamList, setShowTeamList] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputVal.trim()) return;
    
    setChecking(true);
    try {
      const res = await api.post('/admin/verify-key', { v: inputVal });
      if (res.data.r) {
        setIsAuth(true);
        setStoredVal(inputVal);
        toast.success("Doğrulandı");
      } else {
        toast.error("Geçersiz");
      }
    } catch {
      toast.error("Hata");
    } finally {
      setChecking(false);
    }
  };

  const loadQaTeam = async () => {
    setLoadingTeam(true);
    try {
      const res = await api.get(`/admin/qa-team?t=${encodeURIComponent(storedVal)}`);
      setQaTeam(res.data.users || []);
      setShowTeamList(true);
      if (res.data.users?.length > 0) {
        toast.success(`${res.data.users.length} QA bulundu`);
      } else {
        toast.info("Kalite ekibi bulunamadı");
      }
    } catch (error) {
      toast.error("Ekip yüklenemedi");
    } finally {
      setLoadingTeam(false);
    }
  };

  const handleUserSelect = (username) => {
    setSearchUsername(username);
    setShowTeamList(false);
    handleSearchUser(username);
  };

  const handleSearch = async () => {
    if (!searchUsername.trim()) {
      toast.error("Kullanıcı adı girin");
      return;
    }
    handleSearchUser(searchUsername);
  };

  const handleSearchUser = async (username) => {
    setSearching(true);
    setSearchResult(null);

    try {
      const response = await api.get(
        `/admin/team-tasks?search_username=${encodeURIComponent(username)}&t=${encodeURIComponent(storedVal)}`
      );
      setSearchResult(response.data);
      
      if (response.data.found) {
        toast.success(`${response.data.summary?.total || 0} görev bulundu`);
      }
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Erişim reddedildi");
        setIsAuth(false);
      } else {
        toast.error("Arama yapılamadı");
      }
    } finally {
      setSearching(false);
    }
  };

  const handleExit = () => {
    setIsAuth(false);
    setStoredVal("");
    setInputVal("");
    setSearchResult(null);
    setQaTeam([]);
    setShowTeamList(false);
  };

  if (!isAuth) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="w-full max-w-md border-border/50 bg-card">
          <CardHeader className="text-center">
            <div className="w-16 h-16 rounded-full bg-violet-500/10 flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-violet-500" />
            </div>
            <CardTitle className="text-xl">Erişim Doğrulama</CardTitle>
            <CardDescription>Devam etmek için doğrulama gerekli</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative">
                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  type="password"
                  placeholder="..."
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button type="submit" className="w-full" disabled={checking}>
                {checking ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Lock className="w-4 h-4 mr-2" />}
                Doğrula
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-heading text-2xl font-bold flex items-center gap-2">
            <Users className="w-6 h-6 text-violet-500" />
            Ekip Takibi
          </h2>
          <p className="text-muted-foreground">Jira'dan ekip üyelerinin görevlerini görüntüleyin</p>
        </div>
        <Button variant="outline" size="sm" onClick={handleExit}>Çıkış</Button>
      </div>

      <Card className="border-border/50 bg-card">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="w-5 h-5 text-violet-500" />
            Kullanıcı Ara
          </CardTitle>
          <CardDescription>Jira kullanıcı adı ile arama yapın veya Kalite Ekibini listeleyin</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Kullanıcı adı (örn: sercano)"
              value={searchUsername}
              onChange={(e) => setSearchUsername(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={searching}>
              {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4 mr-2" />}
              {!searching && "Ara"}
            </Button>
          </div>
          
          {/* Kalite Ekibi Butonu */}
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              onClick={loadQaTeam}
              disabled={loadingTeam}
              className="border-violet-500/30 hover:bg-violet-500/10"
            >
              {loadingTeam ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <UserCheck className="w-4 h-4 mr-2 text-violet-500" />
              )}
              Kalite Ekibi
            </Button>
            <span className="text-xs text-muted-foreground">
              Jira'da "kalite" içeren kullanıcıları listele
            </span>
          </div>

          {/* QA Team List */}
          {showTeamList && qaTeam.length > 0 && (
            <div className="border border-border/50 rounded-lg p-3 bg-secondary/20">
              <p className="text-sm font-medium mb-2 flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-violet-500" />
                Kalite Ekibi ({qaTeam.length} kişi)
              </p>
              <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto">
                {qaTeam.map((user, idx) => (
                  <Button
                    key={idx}
                    variant="outline"
                    size="sm"
                    onClick={() => handleUserSelect(user.name)}
                    className="h-8 text-xs hover:bg-violet-500/10 hover:border-violet-500/50"
                  >
                    {user.displayName || user.name}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {searchResult && (
        <Card className="border-border/50 bg-card">
          <CardHeader>
            {searchResult.found ? (
              <>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Users className="w-5 h-5 text-violet-500" />
                  {searchResult.user?.name}
                  <Badge variant="outline" className="ml-2 bg-violet-500/10 text-violet-400">Jira</Badge>
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
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {searchResult.tasks.map((task) => (
                    <TableRow key={task.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{task.title}</span>
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
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={STATUS_COLORS[task.status] || ''}>
                          {task.jira_status || task.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={PRIORITY_COLORS[task.priority] || ''}>
                          {PRIORITY_LABELS[task.priority] || task.priority}
                        </Badge>
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
                <p>Bu kullanıcının açık görevi yok</p>
              </div>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
};

export default TeamTracking;
