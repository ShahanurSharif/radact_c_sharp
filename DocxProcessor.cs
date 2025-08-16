using DocumentFormat.OpenXml.Packaging;
using System.Text;

namespace Radact;

// DOCX document processor
public class DocxProcessor : CommonProcessor
{
    public DocxProcessor(DocumentRedactor redactor) : base(redactor) { }

    protected override string ReadContent(string filePath)
    {
        var content = new StringBuilder();

        using (WordprocessingDocument wordDoc = WordprocessingDocument.Open(filePath, false))
        {
            DocumentFormat.OpenXml.Wordprocessing.Body? body = wordDoc.MainDocumentPart?.Document?.Body;
            if (body != null)
            {
                foreach (var paragraph in body.Elements<DocumentFormat.OpenXml.Wordprocessing.Paragraph>())
                {
                    foreach (var run in paragraph.Elements<DocumentFormat.OpenXml.Wordprocessing.Run>())
                    {
                        foreach (var text in run.Elements<DocumentFormat.OpenXml.Wordprocessing.Text>())
                        {
                            content.Append(text.Text);
                        }
                    }
                    content.AppendLine();
                }
            }
        }

        return content.ToString();
    }

    protected override string GenerateOutputPath(string inputFilePath)
    {
        string fileName = Path.GetFileNameWithoutExtension(inputFilePath);
        return Path.Combine("docs", $"redact_{fileName}.docx");
    }

    protected override Task SaveContent(string inputFilePath, string outputPath, string redactedContent)
    {
        // Copy the original file to the output location first
        File.Copy(inputFilePath, outputPath, true);
        
        // Now modify the copied file with redacted content
        using (WordprocessingDocument wordDoc = WordprocessingDocument.Open(outputPath, true))
        {
            var body = wordDoc.MainDocumentPart?.Document?.Body;
            if (body != null)
            {
                // Clear existing content
                body.RemoveAllChildren();

                // Insert redacted content
                var paragraphs = redactedContent.Split(new[] { "\r\n", "\r", "\n" }, StringSplitOptions.None);
                foreach (var paragraphText in paragraphs)
                {
                    var paragraph = new DocumentFormat.OpenXml.Wordprocessing.Paragraph();
                    var run = new DocumentFormat.OpenXml.Wordprocessing.Run();
                    run.Append(new DocumentFormat.OpenXml.Wordprocessing.Text(paragraphText));
                    paragraph.Append(run);
                    body.Append(paragraph);
                }

                wordDoc.MainDocumentPart?.Document?.Save();
            }
        }
        
        return Task.CompletedTask;
    }
}
