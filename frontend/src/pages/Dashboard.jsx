import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  ListTodo,
  Plus,
  ArrowRight,
  Activity,
  TrendingUp,
  Bug
} from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "../lib/utils";

const statusLabels = {
  todo: "Yapılacak",
  in_progress: "Devam Ediyor",
  completed: "Tamamlandı"
};

const priorityLabels = {
  low: "Düşük",
  medium: "Orta",
  high: "Yüksek",
  critical: "Kritik"
};

const priorityColors = {
  low: "bg-muted text-muted-foreground",
  medium: "bg-warning/20 text-warning",
  high: "bg-primary/20 text-primary",
  critical: "bg-destructive/20 text-destructive"
};

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.get("/dashboard/stats");
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryName = (categoryId) => {
    const category = user?.categories?.find(c => c.id === categoryId);
    return category?.name || categoryId;
  };

  const getCategoryColor = (categoryId) => {
    const category = user?.categories?.find(c => c.id === categoryId);
    return category?.color || "#3B82F6";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Welcome Section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="font-heading text-2xl font-bold">
            Hoş geldin, {user?.name?.split(" ")[0]}!
          </h2>
          <p className="text-muted-foreground">
            İşte bugünkü özet görünümün
          </p>
        </div>
        <Button asChild className="btn-glow" data-testid="new-task-btn">
          <Link to="/tasks">
            <Plus className="w-4 h-4 mr-2" />
            Yeni Görev
          </Link>
        </Button>
      </div>

      {/* Stats Grid - Bento Style */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-4">
        {/* Main Progress Card */}
        <Card className="lg:col-span-8 row-span-2 card-hover border-border/50 bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 font-heading">
              <Activity className="w-5 h-5 text-primary" />
              Haftalık İlerleme
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-end gap-4">
              <span className="font-heading text-6xl font-bold text-primary">
                {stats?.completion_rate || 0}%
              </span>
              <span className="text-muted-foreground pb-2">tamamlandı</span>
            </div>
            <Progress value={stats?.completion_rate || 0} className="h-3" />
            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4">
              <div className="text-center p-4 rounded-lg bg-secondary/50">
                <ListTodo className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
                <p className="text-2xl font-bold">{stats?.todo_tasks || 0}</p>
                <p className="text-xs text-muted-foreground">Yapılacak</p>
              </div>
              <div className="text-center p-4 rounded-lg bg-info/10">
                <Clock className="w-6 h-6 mx-auto mb-2 text-info" />
                <p className="text-2xl font-bold">{stats?.in_progress_tasks || 0}</p>
                <p className="text-xs text-muted-foreground">Devam Eden</p>
              </div>
              <div className="text-center p-4 rounded-lg bg-success/10">
                <CheckCircle2 className="w-6 h-6 mx-auto mb-2 text-success" />
                <p className="text-2xl font-bold">{stats?.completed_tasks || 0}</p>
                <p className="text-xs text-muted-foreground">Tamamlanan</p>
              </div>
              <div className="text-center p-4 rounded-lg bg-destructive/10">
                <AlertTriangle className="w-6 h-6 mx-auto mb-2 text-destructive" />
                <p className="text-2xl font-bold">{stats?.overdue_tasks || 0}</p>
                <p className="text-xs text-muted-foreground">Geciken</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="lg:col-span-4 card-hover border-border/50 bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="font-heading text-base">Hızlı İşlemler</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="secondary" className="w-full justify-start" asChild data-testid="quick-new-task">
              <Link to="/tasks">
                <Plus className="w-4 h-4 mr-2" />
                Yeni Görev Ekle
              </Link>
            </Button>
            <Button variant="secondary" className="w-full justify-start" asChild data-testid="quick-calendar">
              <Link to="/calendar">
                <Clock className="w-4 h-4 mr-2" />
                Takvimi Görüntüle
              </Link>
            </Button>
            <Button variant="secondary" className="w-full justify-start" asChild data-testid="quick-reports">
              <Link to="/reports">
                <TrendingUp className="w-4 h-4 mr-2" />
                Raporları İncele
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Category Stats */}
        <Card className="lg:col-span-4 card-hover border-border/50 bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 font-heading text-base">
              <Bug className="w-4 h-4 text-primary" />
              Kategorilere Göre
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {user?.categories?.slice(0, 4).map((category) => (
                <div key={category.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: category.color }}
                    />
                    <span className="text-sm">{category.name}</span>
                  </div>
                  <Badge variant="secondary" className="font-mono">
                    {stats?.category_stats?.[category.id] || 0}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Tasks */}
      <Card className="card-hover border-border/50 bg-card">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="font-heading">Son Görevler</CardTitle>
          <Button variant="ghost" size="sm" asChild data-testid="view-all-tasks">
            <Link to="/tasks">
              Tümünü Gör
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent>
          {stats?.recent_tasks?.length > 0 ? (
            <div className="space-y-3">
              {stats.recent_tasks.map((task, index) => (
                <div
                  key={task.id}
                  className={cn(
                    "flex items-center justify-between p-3 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors",
                    `animate-slideIn stagger-${index + 1}`
                  )}
                  style={{ animationFillMode: "both" }}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: getCategoryColor(task.category_id) }}
                    />
                    <div>
                      <p className="font-medium">{task.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {getCategoryName(task.category_id)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={cn("text-xs", priorityColors[task.priority])}>
                      {priorityLabels[task.priority]}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {statusLabels[task.status]}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <ListTodo className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Henüz görev yok</p>
              <Button variant="link" asChild className="mt-2">
                <Link to="/tasks">İlk görevinizi oluşturun</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
