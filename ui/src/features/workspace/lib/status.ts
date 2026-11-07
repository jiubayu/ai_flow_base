// 首版应用只有草稿状态；未知状态原样展示，避免前端硬编码枚举与服务端脱节。
const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
};

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}
