import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { motion } from "framer-motion";
import { 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  ListTodo,
  Plus,
  ArrowRight,
  Target,
  AlertCircle
} from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "../lib/utils";

// Animation variants
const containerVariants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.1 }
  }
};

const itemVariants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
};

const cardHoverVariants = {
  rest: { scale: 1 },
  hover: { scale: 1.02, transition: { duration: 0.2 } }
};

const statusLabels = {
  backlog: "Backlog",
  today_planned: "Bugün Planlanan",
  in_progress: "Devam Ediyor",
  blocked: "Bloke",
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

  const todayFocus = stats?.today_focus;
  const hasFocusTasks = todayFocus?.tasks?.length > 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <motion.div 
      className="space-y-6"
      initial="initial"
      animate="animate"
      variants={containerVariants}
    >
      {/* Welcome + Action */}
      <motion.div 
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
        variants={itemVariants}
      >
        <div>
          <h2 className="font-heading text-2xl font-bold">
            Günaydın, {user?.name?.split(" ")[0]}
          </h2>
          <p className="text-muted-foreground">
            {hasFocusTasks 
              ? `${todayFocus.total_attention_needed} görev dikkatini bekliyor`
              : "Bugün için acil görev yok"
            }
          </p>
        </div>
        <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
          <Button asChild className="btn-glow" data-testid="new-task-btn">
            <Link to="/tasks">
              <Plus className="w-4 h-4 mr-2" />
              Yeni Görev
            </Link>
          </Button>
        </motion.div>
      </motion.div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* TODAY FOCUS - Hero Card */}
        <motion.div className="lg:col-span-8" variants={itemVariants}>
          <Card className="border-border/50 bg-card h-full" data-testid="today-focus-card">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 font-heading">
              <Target className="w-5 h-5 text-primary" />
              Bugün Odaklan
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Summary Messages */}
            {todayFocus?.summary?.length > 0 && (
              <div className="mb-4 p-3 rounded-lg bg-warning/10 border border-warning/20">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-warning mt-0.5 shrink-0" />
                  <div className="text-sm text-warning">
                    {todayFocus.summary.map((msg, i) => (
                      <p key={i}>{msg}</p>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Focus Tasks */}
            {hasFocusTasks ? (
              <div className="space-y-2">
                {todayFocus.tasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors group"
                  >
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <div
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ backgroundColor: getCategoryColor(task.category_id) }}
                      />
                      <div className="min-w-0">
                        <p className="font-medium truncate">{task.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {getCategoryName(task.category_id)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {task.focus_labels?.map((label, i) => (
                        <Badge 
                          key={i}
                          variant="outline" 
                          className={cn(
                            "text-xs",
                            label.includes("gecikmiş") && "border-destructive/50 text-destructive",
                            label.includes("son gün") && "border-warning/50 text-warning",
                            label.includes("Yarın") && "border-info/50 text-info"
                          )}
                        >
                          {label}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ))}
                
                {todayFocus.total_attention_needed > 5 && (
                  <p className="text-xs text-muted-foreground text-center pt-2">
                    +{todayFocus.total_attention_needed - 5} görev daha
                  </p>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-success opacity-70" />
                <p className="text-muted-foreground">Harika! Acil görev yok.</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Bugün rahat bir gün geçirebilirsin.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
        </motion.div>

        {/* Quick Stats */}
        <motion.div className="lg:col-span-4 space-y-4" variants={itemVariants}>
          {/* Progress Card */}
          <motion.div whileHover={{ scale: 1.02 }} transition={{ duration: 0.2 }}>
            <Card className="border-border/50 bg-card">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Tamamlanma</span>
                <span className="font-heading text-2xl font-bold text-primary">
                  {stats?.completion_rate || 0}%
                </span>
              </div>
              <Progress value={stats?.completion_rate || 0} className="h-2" />
              <p className="text-xs text-muted-foreground mt-2">
                {stats?.completed_tasks || 0} / {stats?.total_tasks || 0} görev
              </p>
            </CardContent>
          </Card>
          </motion.div>

          {/* Status Summary */}
          <motion.div whileHover={{ scale: 1.02 }} transition={{ duration: 0.2 }}>
            <Card className="border-border/50 bg-card">
              <CardContent className="pt-6 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ListTodo className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">Yapılacak</span>
                  </div>
                  <span className="font-mono text-sm">{stats?.todo_tasks || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-info" />
                    <span className="text-sm">Devam Eden</span>
                  </div>
                  <span className="font-mono text-sm">{stats?.in_progress_tasks || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-success" />
                    <span className="text-sm">Tamamlanan</span>
                  </div>
                  <span className="font-mono text-sm">{stats?.completed_tasks || 0}</span>
                </div>
                {stats?.overdue_tasks > 0 && (
                  <div className="flex items-center justify-between pt-2 border-t border-border/50">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-destructive" />
                      <span className="text-sm text-destructive">Geciken</span>
                    </div>
                    <span className="font-mono text-sm text-destructive">{stats?.overdue_tasks}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
      </div>

      {/* Recent Activity - Simplified */}
      <motion.div variants={itemVariants}>
        <Card className="border-border/50 bg-card">
        <CardHeader className="flex flex-row items-center justify-between py-4">
          <CardTitle className="font-heading text-base">Son Eklenenler</CardTitle>
          <Button variant="ghost" size="sm" asChild data-testid="view-all-tasks">
            <Link to="/tasks">
              Tümü
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent className="pt-0">
          {stats?.recent_tasks?.length > 0 ? (
            <div className="space-y-2">
              {stats.recent_tasks.slice(0, 4).map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between py-2 border-b border-border/30 last:border-0"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: getCategoryColor(task.category_id) }}
                    />
                    <span className={cn(
                      "text-sm truncate",
                      task.status === "completed" && "line-through text-muted-foreground"
                    )}>
                      {task.title}
                    </span>
                  </div>
                  <Badge variant="outline" className="text-xs shrink-0">
                    {statusLabels[task.status]}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              Henüz görev yok
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
