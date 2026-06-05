import { useState } from "react";
import { ShieldAlert } from "lucide-react";
import { Dialog } from "@/components/ui/overlay";
import { Button } from "@/components/ui/Button";
import { useAppStore } from "@/store/app";

export function DisclaimerDialog() {
  const accepted = useAppStore((s) => s.disclaimerAccepted);
  const accept = useAppStore((s) => s.acceptDisclaimer);
  const [checked, setChecked] = useState(false);

  return (
    <Dialog open={!accepted} title="使用前须知">
      <div className="space-y-4 text-sm leading-relaxed text-text">
        <div className="flex items-start gap-3 rounded-md bg-warning/10 p-3 text-warning">
          <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" />
          <p>本工具仅用于个人创作辅助与学习研究，请遵守小红书平台规则与相关法律法规。</p>
        </div>
        <ul className="list-disc space-y-1.5 pl-5 text-text-mut">
          <li>请使用本人账号登录，采集默认低频限速，不进行大规模商用数据采集。</li>
          <li>仅采集公开可见内容，不抓取隐私信息。</li>
          <li>仿写结果应进行原创化改写，避免直接搬运侵权。</li>
          <li>因使用本工具产生的任何后果由使用者自行承担。</li>
        </ul>
        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
            className="h-4 w-4 accent-[var(--accent)]"
          />
          <span>我已阅读并同意以上条款</span>
        </label>
        <div className="flex justify-end">
          <Button disabled={!checked} onClick={accept}>
            同意并继续
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
