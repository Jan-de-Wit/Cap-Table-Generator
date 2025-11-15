"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Download, FileSpreadsheet } from "lucide-react";
import type { CapTableData } from "@/types/cap-table";

interface JsonPreviewProps {
  data: CapTableData;
  onDownloadExcel: () => void;
}

export function JsonPreview({ data, onDownloadExcel }: JsonPreviewProps) {
  const [jsonString, setJsonString] = React.useState(
    JSON.stringify(data, null, 2)
  );

  React.useEffect(() => {
    setJsonString(JSON.stringify(data, null, 2));
  }, [data]);

  const handleDownloadJson = () => {
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "cap-table.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>JSON Preview</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleDownloadJson}>
              <Download className="h-4 w-4 mr-2" />
              Download JSON
            </Button>
            <Button onClick={onDownloadExcel}>
              <FileSpreadsheet className="h-4 w-4 mr-2" />
              Generate Excel
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Textarea
          value={jsonString}
          onChange={(e) => setJsonString(e.target.value)}
          className="font-mono text-sm min-h-[400px]"
          readOnly
        />
      </CardContent>
    </Card>
  );
}

