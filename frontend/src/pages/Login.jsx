import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { toast } from "sonner";
import { CheckSquare, Mail, ArrowRight, Loader2 } from "lucide-react";

const Login = () => {
  const [email, setEmail] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email.endsWith("@intertech.com.tr")) {
      toast.error("Sadece @intertech.com.tr uzantılı e-postalar kabul edilir");
      return;
    }

    setLoading(true);
    try {
      if (isRegister) {
        await register(email);
        toast.success("Kayıt başarılı! Hoş geldiniz.");
      } else {
        await login(email);
        toast.success("Giriş başarılı!");
      }
    } catch (error) {
      const message = error.response?.data?.detail || "Bir hata oluştu";
      toast.error(message);
      
      // If login fails with not found, suggest registration
      if (error.response?.status === 404 && !isRegister) {
        setIsRegister(true);
        toast.info("Hesabınız bulunamadı. Kayıt olmayı deneyin.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
      style={{
        backgroundImage: "url('https://images.pexels.com/photos/9951077/pexels-photo-9951077.jpeg')",
        backgroundSize: "cover",
        backgroundPosition: "center"
      }}
    >
      {/* Overlay */}
      <div className="absolute inset-0 bg-background/90 backdrop-blur-sm" />
      
      {/* Content */}
      <div className="relative z-10 w-full max-w-md animate-fadeIn">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/30">
            <CheckSquare className="w-7 h-7 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-heading text-2xl font-bold">QA Task Manager</h1>
            <p className="text-sm text-muted-foreground">Intertech QA Ekibi</p>
          </div>
        </div>

        <Card className="glass border-border/50 shadow-2xl">
          <CardHeader className="text-center pb-2">
            <CardTitle className="font-heading text-2xl">
              {isRegister ? "Hesap Oluştur" : "Giriş Yap"}
            </CardTitle>
            <CardDescription>
              Şirket e-postanızla devam edin
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Şirket E-postası</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="isim.soyisim@intertech.com.tr"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 h-12 bg-secondary/50 border-border/50 focus:border-primary"
                    required
                    data-testid="email-input"
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Sadece @intertech.com.tr uzantılı e-postalar kabul edilir
                </p>
              </div>

              <Button
                type="submit"
                className="w-full h-12 btn-glow font-semibold"
                disabled={loading}
                data-testid="submit-btn"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    {isRegister ? "Kayıt Ol" : "Giriş Yap"}
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </>
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <button
                type="button"
                onClick={() => setIsRegister(!isRegister)}
                className="text-sm text-muted-foreground hover:text-primary transition-colors"
                data-testid="toggle-auth-mode"
              >
                {isRegister
                  ? "Zaten hesabınız var mı? Giriş yapın"
                  : "Hesabınız yok mu? Kayıt olun"}
              </button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground mt-6">
          © 2025 Intertech QA Task Manager
        </p>
      </div>
    </div>
  );
};

export default Login;
