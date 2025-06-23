"use client";

import { Icons } from "@v1/ui/icons";
import { useState, useEffect } from "react";
import { useCopyToClipboard } from "usehooks-ts";

export function CopyText({ value }: { value: string }) {
  const [_, copy] = useCopyToClipboard();
  const [copied, setCopied] = useState(false);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const handleCopy = () => {
    copy(value);
    setCopied(true);

    setTimeout(() => setCopied(false), 2000);
  };

  if (!isClient) {
    return (
      <button
        type="button"
        className="font-mono text-[#878787] text-xs md:text-sm p-4 rounded-full border border-border transition-colors flex items-center gap-2 bg-background"
      >
        <span>{value}</span>
        <Icons.Copy className="size-3.5" />
      </button>
    );
  }

  return (
    <button
      onClick={handleCopy}
      type="button"
      className="font-mono text-[#878787] text-xs md:text-sm p-4 rounded-full border border-border transition-colors flex items-center gap-2 bg-background"
    >
      <span>{value}</span>
      {copied ? (
        <Icons.Check className="size-3.5" />
      ) : (
        <Icons.Copy className="size-3.5" />
      )}
    </button>
  );
}
