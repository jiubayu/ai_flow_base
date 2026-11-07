import { TOKEN_GROUPS, type TokenCategory } from "@/shared/components/theme/theme-tokens";
import { ThemeShowcaseShell } from "./ThemeShowcaseShell";

const swatchCategories = new Set<TokenCategory>(["text", "background", "border", "accent"]);

export function ThemeTokenGallery() {
  return (
    <ThemeShowcaseShell
      title="Token 分类"
      subtitle="按语义分类的主题 token：开发者应从这里定位所需语义，而非硬编码色值。"
    >
      <div className="grid gap-t-4 sm:grid-cols-2">
        {TOKEN_GROUPS.map((group) => (
          <div key={group.group_name} className="rounded-md border border-edge-weak bg-surface-page p-t-4">
            <h3 className="text-level-3 font-semibold">{group.group_name}</h3>
            <p className="mt-t-1 text-level-4">{group.description}</p>
            <ul className="mt-t-3 space-y-t-2">
              {group.tokens.map((token) => (
                <li key={token.name} className="flex items-center gap-t-2 text-body-sm text-content-secondary">
                  {swatchCategories.has(token.category) ? (
                    <span
                      className="h-4 w-4 shrink-0 rounded-sm border border-edge-base"
                      style={{ background: token.value }}
                    />
                  ) : null}
                  <span className="font-mono text-caption text-content-primary">{token.name}</span>
                  <span className="text-level-4">{token.semantic_role}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </ThemeShowcaseShell>
  );
}
