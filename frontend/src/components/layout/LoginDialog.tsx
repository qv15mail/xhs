import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, QrCode, RefreshCw } from "lucide-react";
import { Dialog } from "@/components/ui/overlay";
import { Button } from "@/components/ui/Button";
import { api } from "@/api/client";
import { useAppStore } from "@/store/app";

type Phase = "loading" | "waiting" | "success" | "expired" | "error";

export function LoginDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const setLoggedIn = useAppStore((s) => s.setLoggedIn);
  const [phase, setPhase] = useState<Phase>("loading");
  const [qrcode, setQrcode] = useState("");
  const [note, setNote] = useState("");
  const pollRef = useRef<number | null>(null);

  const stopPoll = useCallback(() => {
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startQrcode = useCallback(async () => {
    stopPoll();
    setPhase("loading");
    setQrcode("");
    try {
      const res = await api.loginQrcode();
      if (res.loggedIn) {
        setLoggedIn(true);
        setPhase("success");
        setNote(res.note || "已登录");
        return;
      }
      if (!res.qrcode) {
        setPhase("error");
        setNote(res.note || "获取二维码失败");
        return;
      }
      setQrcode(res.qrcode);
      setNote(res.note);
      setPhase("waiting");
      pollRef.current = window.setInterval(async () => {
        try {
          const st = await api.authStatus();
          if (st.loggedIn) {
            stopPoll();
            setLoggedIn(true);
            setPhase("success");
          } else if (st.status === "expired") {
            stopPoll();
            setPhase("expired");
          } else if (st.status === "error") {
            stopPoll();
            setPhase("error");
            setNote(st.error || "登录失败");
          }
        } catch {
          /* 网络抖动忽略，继续轮询 */
        }
      }, 2000);
    } catch (e) {
      setPhase("error");
      setNote(e instanceof Error ? e.message : "获取二维码失败");
    }
  }, [setLoggedIn, stopPoll]);

  useEffect(() => {
    if (open) startQrcode();
    return stopPoll;
  }, [open, startQrcode, stopPoll]);

  useEffect(() => {
    if (phase === "success") {
      const t = window.setTimeout(onClose, 800);
      return () => window.clearTimeout(t);
    }
  }, [phase, onClose]);

  return (
    <Dialog open={open} onClose={onClose} title="扫码登录小红书">
      <div className="flex flex-col items-center gap-4 py-2">
        <div className="flex h-52 w-52 items-center justify-center rounded-lg border border-border bg-bg">
          {phase === "loading" && <Loader2 className="h-8 w-8 animate-spin text-text-mut" />}
          {phase === "waiting" && qrcode && (
            <img src={qrcode} alt="登录二维码" className="h-48 w-48 rounded-md" />
          )}
          {(phase === "expired" || phase === "error") && (
            <div className="flex flex-col items-center gap-2 text-text-mut">
              <QrCode className="h-10 w-10" />
              <span className="text-sm">{phase === "expired" ? "二维码已过期" : "获取失败"}</span>
            </div>
          )}
          {phase === "success" && (
            <div className="flex flex-col items-center gap-2 text-success">
              <QrCode className="h-10 w-10" />
              <span className="text-sm font-medium">登录成功</span>
            </div>
          )}
        </div>

        <p className="text-center text-sm text-text-mut">
          {phase === "loading" && "正在打开登录页并获取二维码…"}
          {phase === "waiting" && (note || "请使用小红书 App 扫描二维码登录")}
          {phase === "success" && "登录态已保存，可直接用于采集"}
          {phase === "expired" && "请点击下方按钮刷新二维码"}
          {phase === "error" && (note || "登录失败，请重试")}
        </p>

        {(phase === "expired" || phase === "error") && (
          <Button variant="secondary" size="sm" onClick={startQrcode}>
            <RefreshCw className="h-4 w-4" />
            刷新二维码
          </Button>
        )}
      </div>
    </Dialog>
  );
}
