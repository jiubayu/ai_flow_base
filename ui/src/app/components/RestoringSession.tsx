// 会话恢复期间守卫不请求受保护数据。
export function RestoringSession() {
  return (
    <p className="text-body-sm text-content-secondary" role="status">
      正在恢复当前浏览器会话…
    </p>
  );
}
