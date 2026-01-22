import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import api from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Calendar } from "../components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "../components/ui/popover";
import { toast } from "sonner";
import { 
  Plus, 
  Search, 
  Filter,
  MoreVertical,
  Edit,
  Trash2,
  CheckCircle2,
  Clock,
  ListTodo,
  CalendarIcon,
  Loader2
} from "lucide-react";
import { cn } from "../lib/utils";
import { format } from "date-fns";
import { tr } from "date-fns/locale";

const statusLabels = {
  todo: "Yapılacak",
  in_progress: "Devam Ediyor",
  completed: "Tamamlandı"
};

const statusIcons = {
  todo: ListTodo,
  in_progress: Clock,
  completed: CheckCircle2
};

const statusColors = {
  todo: "bg-muted text-muted-foreground",
  in_progress: "bg-info/20 text-info border-info/30",
  completed: "bg-success/20 text-success border-success/30"
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

const Tasks = () => {
  const { user } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterPriority, setFilterPriority] = useState("all");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [saving, setSaving] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    category_id: "",
    project_id: "",
    priority: "medium",
    due_date: null
  });

  useEffect(() => {
    fetchTasks();
    fetchProjects();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await api.get("/tasks");
      setTasks(response.data);
    } catch (error) {
      toast.error("Görevler yüklenirken hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await api.get("/projects");
      setProjects(response.data);
    } catch (error) {
      console.error("Error fetching projects:", error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      const payload = {
        ...formData,
        due_date: formData.due_date ? formData.due_date.toISOString() : null,
        project_id: formData.project_id === "none" ? null : formData.project_id
      };
      
      if (editingTask) {
        await api.put(`/tasks/${editingTask.id}`, payload);
        toast.success("Görev güncellendi");
      } else {
        await api.post("/tasks", payload);
        toast.success("Görev oluşturuldu");
      }
      
      setIsDialogOpen(false);
      resetForm();
      fetchTasks();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Bir hata oluştu");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (task) => {
    setEditingTask(task);
    setFormData({
      title: task.title,
      description: task.description || "",
      category_id: task.category_id,
      project_id: task.project_id || "none",
      priority: task.priority,
      due_date: task.due_date ? new Date(task.due_date) : null
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (taskId) => {
    if (!window.confirm("Bu görevi silmek istediğinize emin misiniz?")) return;
    
    try {
      await api.delete(`/tasks/${taskId}`);
      toast.success("Görev silindi");
      fetchTasks();
    } catch (error) {
      toast.error("Görev silinirken hata oluştu");
    }
  };

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await api.put(`/tasks/${taskId}`, { status: newStatus });
      toast.success("Durum güncellendi");
      fetchTasks();
    } catch (error) {
      toast.error("Durum güncellenirken hata oluştu");
    }
  };

  const resetForm = () => {
    setEditingTask(null);
    setFormData({
      title: "",
      description: "",
      category_id: user?.categories?.[0]?.id || "",
      project_id: "",
      priority: "medium",
      due_date: null
    });
  };

  const getCategoryName = (categoryId) => {
    const category = user?.categories?.find(c => c.id === categoryId);
    return category?.name || categoryId;
  };

  const getCategoryColor = (categoryId) => {
    const category = user?.categories?.find(c => c.id === categoryId);
    return category?.color || "#3B82F6";
  };

  const getProjectName = (projectId) => {
    const project = projects.find(p => p.id === projectId);
    return project?.name || "";
  };

  const filteredTasks = tasks.filter(task => {
    const matchesSearch = task.title.toLowerCase().includes(search.toLowerCase()) ||
                         task.description?.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = filterStatus === "all" || task.status === filterStatus;
    const matchesCategory = filterCategory === "all" || task.category_id === filterCategory;
    const matchesPriority = filterPriority === "all" || task.priority === filterPriority;
    
    return matchesSearch && matchesStatus && matchesCategory && matchesPriority;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="font-heading text-2xl font-bold">Görevler</h2>
          <p className="text-muted-foreground">{tasks.length} görev</p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={(open) => {
          setIsDialogOpen(open);
          if (!open) resetForm();
        }}>
          <DialogTrigger asChild>
            <Button className="btn-glow" data-testid="new-task-dialog-btn">
              <Plus className="w-4 h-4 mr-2" />
              Yeni Görev
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle className="font-heading">
                {editingTask ? "Görevi Düzenle" : "Yeni Görev"}
              </DialogTitle>
              <DialogDescription>
                Görev detaylarını girin
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Başlık</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Görev başlığı"
                  required
                  data-testid="task-title-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Açıklama</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Görev açıklaması (opsiyonel)"
                  rows={3}
                  data-testid="task-description-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Kategori</Label>
                  <Select
                    value={formData.category_id}
                    onValueChange={(value) => setFormData({ ...formData, category_id: value })}
                  >
                    <SelectTrigger data-testid="task-category-select">
                      <SelectValue placeholder="Kategori seçin" />
                    </SelectTrigger>
                    <SelectContent>
                      {user?.categories?.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: cat.color }}
                            />
                            {cat.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Öncelik</Label>
                  <Select
                    value={formData.priority}
                    onValueChange={(value) => setFormData({ ...formData, priority: value })}
                  >
                    <SelectTrigger data-testid="task-priority-select">
                      <SelectValue placeholder="Öncelik seçin" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(priorityLabels).map(([key, label]) => (
                        <SelectItem key={key} value={key}>{label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Proje</Label>
                  <Select
                    value={formData.project_id || "none"}
                    onValueChange={(value) => setFormData({ ...formData, project_id: value })}
                  >
                    <SelectTrigger data-testid="task-project-select">
                      <SelectValue placeholder="Proje seçin" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Proje yok</SelectItem>
                      {projects.map((project) => (
                        <SelectItem key={project.id} value={project.id}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Bitiş Tarihi</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          "w-full justify-start text-left font-normal",
                          !formData.due_date && "text-muted-foreground"
                        )}
                        data-testid="task-due-date-btn"
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {formData.due_date 
                          ? format(formData.due_date, "d MMM yyyy", { locale: tr })
                          : "Tarih seçin"
                        }
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={formData.due_date}
                        onSelect={(date) => setFormData({ ...formData, due_date: date })}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>

              {editingTask && (
                <div className="space-y-2">
                  <Label>Durum</Label>
                  <Select
                    value={formData.status || editingTask.status}
                    onValueChange={(value) => setFormData({ ...formData, status: value })}
                  >
                    <SelectTrigger data-testid="task-status-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(statusLabels).map(([key, label]) => (
                        <SelectItem key={key} value={key}>{label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  İptal
                </Button>
                <Button type="submit" disabled={saving} data-testid="task-submit-btn">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : (editingTask ? "Güncelle" : "Oluştur")}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card className="border-border/50 bg-card">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Görev ara..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
                data-testid="task-search-input"
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[140px]" data-testid="filter-status">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Durum" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tüm Durumlar</SelectItem>
                  {Object.entries(statusLabels).map(([key, label]) => (
                    <SelectItem key={key} value={key}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Select value={filterCategory} onValueChange={setFilterCategory}>
                <SelectTrigger className="w-[140px]" data-testid="filter-category">
                  <SelectValue placeholder="Kategori" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tüm Kategoriler</SelectItem>
                  {user?.categories?.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              <Select value={filterPriority} onValueChange={setFilterPriority}>
                <SelectTrigger className="w-[140px]" data-testid="filter-priority">
                  <SelectValue placeholder="Öncelik" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tüm Öncelikler</SelectItem>
                  {Object.entries(priorityLabels).map(([key, label]) => (
                    <SelectItem key={key} value={key}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Task List */}
      <div className="space-y-3">
        {filteredTasks.length > 0 ? (
          filteredTasks.map((task, index) => {
            const StatusIcon = statusIcons[task.status];
            return (
              <Card 
                key={task.id} 
                className={cn(
                  "card-hover border-border/50 bg-card animate-slideIn",
                  `stagger-${(index % 5) + 1}`
                )}
                style={{ animationFillMode: "both" }}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <button
                        onClick={() => handleStatusChange(
                          task.id, 
                          task.status === "completed" ? "todo" : 
                          task.status === "todo" ? "in_progress" : "completed"
                        )}
                        className={cn(
                          "mt-1 p-1 rounded-full border transition-colors",
                          statusColors[task.status]
                        )}
                        data-testid={`task-status-toggle-${task.id}`}
                      >
                        <StatusIcon className="w-4 h-4" />
                      </button>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className={cn(
                            "font-medium",
                            task.status === "completed" && "line-through text-muted-foreground"
                          )}>
                            {task.title}
                          </h3>
                          <Badge 
                            variant="outline" 
                            className="text-xs"
                            style={{ borderColor: getCategoryColor(task.category_id), color: getCategoryColor(task.category_id) }}
                          >
                            {getCategoryName(task.category_id)}
                          </Badge>
                        </div>
                        {task.description && (
                          <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                            {task.description}
                          </p>
                        )}
                        <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground flex-wrap">
                          {task.project_id && (
                            <span className="font-mono bg-secondary px-2 py-0.5 rounded">
                              {getProjectName(task.project_id)}
                            </span>
                          )}
                          {task.due_date && (
                            <span className="flex items-center gap-1">
                              <CalendarIcon className="w-3 h-3" />
                              {format(new Date(task.due_date), "d MMM yyyy", { locale: tr })}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={cn("text-xs", priorityColors[task.priority])}>
                        {priorityLabels[task.priority]}
                      </Badge>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8" data-testid={`task-menu-${task.id}`}>
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleEdit(task)} data-testid={`task-edit-${task.id}`}>
                            <Edit className="w-4 h-4 mr-2" />
                            Düzenle
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(task.id)} 
                            className="text-destructive"
                            data-testid={`task-delete-${task.id}`}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Sil
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })
        ) : (
          <Card className="border-border/50 bg-card">
            <CardContent className="p-8 text-center">
              <ListTodo className="w-12 h-12 mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">
                {search || filterStatus !== "all" || filterCategory !== "all" || filterPriority !== "all"
                  ? "Filtrelere uygun görev bulunamadı"
                  : "Henüz görev yok. İlk görevinizi oluşturun!"}
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default Tasks;
