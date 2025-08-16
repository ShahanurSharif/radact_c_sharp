using iText.Kernel.Pdf;
using iText.Kernel.Pdf.Canvas.Parser;
using System.Text;
using System.Text.RegularExpressions;

namespace Radact;

// PDF document processor
public class PdfProcessor : CommonProcessor
{
    public PdfProcessor(DocumentRedactor redactor) : base(redactor) { }

    protected override string ReadContent(string filePath)
    {
        var content = new StringBuilder();

        using (PdfReader reader = new PdfReader(filePath))
        using (PdfDocument pdfDoc = new PdfDocument(reader))
        {
            for (int i = 1; i <= pdfDoc.GetNumberOfPages(); i++)
            {
                string pageText = PdfTextExtractor.GetTextFromPage(pdfDoc.GetPage(i));
                
                // Clean up the extracted text
                pageText = CleanExtractedText(pageText);
                
                content.AppendLine(pageText);
            }
        }

        return content.ToString();
    }

    private string CleanExtractedText(string text)
    {
        if (string.IsNullOrEmpty(text))
            return text;

        // Replace multiple tabs and spaces with single space
        text = Regex.Replace(text, @"\t+", " ");
        text = Regex.Replace(text, @" {2,}", " ");
        
        // Fix common character encoding issues
        text = text.Replace("ﬁ", "fi");
        text = text.Replace("�", "fi");
        text = text.Replace("'", "'");
        
        // Clean up line breaks and spacing
        text = Regex.Replace(text, @"\r\n|\r|\n", "\n");
        text = Regex.Replace(text, @"\n\s*\n", "\n\n");
        
        return text.Trim();
    }

    protected override string GenerateOutputPath(string inputFilePath)
    {
        string fileName = Path.GetFileNameWithoutExtension(inputFilePath);
        return Path.Combine("docs", $"redact_{fileName}.pdf");
    }

    protected override Task SaveContent(string inputFilePath, string outputPath, string redactedContent)
    {
        // Always save as text file since PDF creation is problematic
        var textPath = outputPath.Replace(".pdf", "_redacted.txt");
        File.WriteAllText(textPath, redactedContent);
        Console.WriteLine($"✅ Redacted content saved as text: {textPath}");
        
        // Try to create PDF using external method
        try
        {
            CreateSimplePdf(outputPath, redactedContent);
            if (File.Exists(outputPath) && new FileInfo(outputPath).Length > 0)
            {
                Console.WriteLine($"✅ PDF successfully created: {outputPath}");
                Console.WriteLine($"File size: {new FileInfo(outputPath).Length} bytes");
            }
            else
            {
                Console.WriteLine($"⚠️ PDF creation failed, using text file: {textPath}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ PDF creation error: {ex.Message}");
            Console.WriteLine($"💾 Content saved as text file: {textPath}");
        }
        
        return Task.CompletedTask;
    }

    private void CreateSimplePdf(string outputPath, string content)
    {
        // Delete existing file
        if (File.Exists(outputPath))
        {
            File.Delete(outputPath);
        }

        try
        {
            // Create PDF with explicit file stream handling
            using (var fileStream = new FileStream(outputPath, FileMode.Create, FileAccess.Write))
            {
                var writerProperties = new WriterProperties();
                using (var writer = new PdfWriter(fileStream, writerProperties))
                {
                    using (var pdfDoc = new PdfDocument(writer))
                    {
                        pdfDoc.SetDefaultPageSize(iText.Kernel.Geom.PageSize.A4);
                        
                        using (var document = new iText.Layout.Document(pdfDoc))
                        {
                            document.SetMargins(50, 50, 50, 50);
                            
                            // Add title
                            document.Add(new iText.Layout.Element.Paragraph("REDACTED DOCUMENT")
                                .SetFontSize(16)
                                .SetTextAlignment(iText.Layout.Properties.TextAlignment.CENTER)
                                .SetMarginBottom(20));
                            
                            // Add content line by line
                            var lines = content.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
                            
                            if (lines.Length == 0)
                            {
                                // If no content, add a placeholder
                                document.Add(new iText.Layout.Element.Paragraph("No content available")
                                    .SetFontSize(11));
                            }
                            else
                            {
                                foreach (var line in lines)
                                {
                                    if (!string.IsNullOrWhiteSpace(line))
                                    {
                                        document.Add(new iText.Layout.Element.Paragraph(line.Trim())
                                            .SetFontSize(11)
                                            .SetMarginBottom(5));
                                    }
                                }
                            }
                            
                            // Explicitly close the document to ensure content is written
                            document.Close();
                        }
                        // Explicitly close PDF document
                        pdfDoc.Close();
                    }
                    // Explicitly close writer
                    writer.Close();
                }
                // Ensure file stream is flushed
                fileStream.Flush();
            }
            
            Console.WriteLine($"✅ PDF creation completed. Checking file size...");
            
            // Verify the file was actually created with content
            if (File.Exists(outputPath))
            {
                var fileInfo = new FileInfo(outputPath);
                Console.WriteLine($"📄 PDF file size: {fileInfo.Length} bytes");
                
                if (fileInfo.Length == 0)
                {
                    Console.WriteLine("❌ PDF file is empty - creation failed");
                    File.Delete(outputPath); // Remove empty file
                    throw new Exception("PDF file created but is empty");
                }
            }
            else
            {
                throw new Exception("PDF file was not created");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ Detailed PDF creation error: {ex.Message}");
            Console.WriteLine($"❌ Stack trace: {ex.StackTrace}");
            
            // Clean up any partial file
            if (File.Exists(outputPath))
            {
                try
                {
                    File.Delete(outputPath);
                }
                catch
                {
                    // Ignore cleanup errors
                }
            }
            
            throw; // Re-throw to be caught by SaveContent method
        }
    }
}
