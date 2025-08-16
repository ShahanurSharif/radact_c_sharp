using System.Text;
using System.Text.RegularExpressions;
using DocumentFormat.OpenXml.Packaging;
using iText.Kernel.Pdf;
using iText.Kernel.Pdf.Canvas.Parser;

// Main program entry point
try
{
    var processor = new DocumentProcessorFactory();
    await processor.ProcessDocumentAsync("docs/1.docx");
    await processor.ProcessDocumentAsync("docs/1.pdf");
}
catch (Exception ex)
{
    Console.WriteLine($"Error: {ex.Message}");
}

// Factory class to create appropriate document processors
public class DocumentProcessorFactory
{
    private readonly DocumentRedactor _redactor;

    public DocumentProcessorFactory()
    {
        _redactor = new DocumentRedactor();
    }

    public async Task ProcessDocumentAsync(string inputFilePath)
    {
        string extension = Path.GetExtension(inputFilePath).ToLower();
        IDocumentProcessor processor = extension switch
        {
            ".docx" => new DocxProcessor(_redactor),
            ".pdf" => new PdfProcessor(_redactor),
            _ => throw new NotSupportedException($"File format {extension} is not supported")
        };

        await processor.ProcessAsync(inputFilePath);
    }
}

// Common interface for all document processors
public interface IDocumentProcessor
{
    Task ProcessAsync(string inputFilePath);
}

// Common base functionality shared by all processors
public abstract class CommonProcessor : IDocumentProcessor
{
    protected readonly DocumentRedactor Redactor;

    protected CommonProcessor(DocumentRedactor redactor)
    {
        Redactor = redactor;
    }

    public async Task ProcessAsync(string inputFilePath)
    {
        Console.WriteLine($"\nProcessing: {inputFilePath}");
        
        // Read document content
        string originalContent = ReadContent(inputFilePath);
        Console.WriteLine("Document content loaded successfully!");
        Console.WriteLine($"Content length: {originalContent.Length} characters");
        Console.WriteLine("\n--- Original Document Content ---");
        Console.WriteLine(originalContent);

        // Redact sensitive information
        string redactedContent = Redactor.RedactSensitiveInformation(originalContent);

        // Save redacted content
        string outputPath = GenerateOutputPath(inputFilePath);
        await SaveContent(inputFilePath, outputPath, redactedContent);

        Console.WriteLine("\n--- Redacted Document Content ---");
        Console.WriteLine(redactedContent);
        Console.WriteLine($"\nRedacted content saved to: {outputPath}");
    }

    protected abstract string ReadContent(string filePath);
    protected abstract string GenerateOutputPath(string inputFilePath);
    protected abstract Task SaveContent(string inputFilePath, string outputPath, string redactedContent);
}

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

// PDF document processor with improved approach to fix zero-byte issue
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
        // First, always save as text file (guaranteed to work)
        var textPath = outputPath.Replace(".pdf", "_redacted.txt");
        File.WriteAllText(textPath, redactedContent);
        Console.WriteLine($"✅ Redacted content saved as text: {textPath}");
        
        // Then try to create PDF with simplified approach
        try
        {
            CreateSimplePdf(outputPath, redactedContent);
            
            // Verify the PDF was actually created with content
            if (File.Exists(outputPath) && new FileInfo(outputPath).Length > 0)
            {
                Console.WriteLine($"✅ PDF successfully created: {outputPath}");
                Console.WriteLine($"📄 PDF file size: {new FileInfo(outputPath).Length} bytes");
            }
            else
            {
                Console.WriteLine($"⚠️ PDF creation failed - file is empty or not created");
                Console.WriteLine($"💾 Using text file instead: {textPath}");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"❌ PDF creation error: {ex.Message}");
            Console.WriteLine($"💾 Content available in text file: {textPath}");
        }
        
        return Task.CompletedTask;
    }

    private void CreateSimplePdf(string outputPath, string content)
    {
        // Delete existing file to start fresh
        if (File.Exists(outputPath))
        {
            File.Delete(outputPath);
        }

        // Create PDF with minimal configuration to avoid issues
        using (var fileStream = new FileStream(outputPath, FileMode.Create))
        using (var writer = new PdfWriter(fileStream))
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
                    
                    // Add content line by line with basic formatting
                    var lines = content.Split(new[] { '\n', '\r' }, StringSplitOptions.None);
                    
                    foreach (var line in lines)
                    {
                        if (string.IsNullOrWhiteSpace(line))
                        {
                            // Add spacing for empty lines
                            document.Add(new iText.Layout.Element.Paragraph(" ").SetMarginBottom(5));
                        }
                        else
                        {
                            document.Add(new iText.Layout.Element.Paragraph(line.Trim())
                                .SetFontSize(10)
                                .SetMarginBottom(3));
                        }
                    }
                }
            }
        }
    }
}

// Handles redacting sensitive information (shared across all file types)
public class DocumentRedactor
{
    private readonly List<RedactionRule> _redactionRules;

    public DocumentRedactor()
    {
        _redactionRules = InitializeRedactionRules();
    }

    public string RedactSensitiveInformation(string content)
    {
        string redacted = content;

        foreach (var rule in _redactionRules)
        {
            redacted = Regex.Replace(redacted, rule.Pattern, rule.Replacement, rule.Options);
        }

        return redacted;
    }

    private List<RedactionRule> InitializeRedactionRules()
    {
        return new List<RedactionRule>
        {
            new RedactionRule(@"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]"),
            new RedactionRule(@"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b", "[PHONE_REDACTED]"),
            new RedactionRule(@"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]"),
            new RedactionRule(@"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[CREDIT_CARD_REDACTED]"),
            new RedactionRule(@"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", "[DATE_REDACTED]"),
            new RedactionRule(@"\b(?:password|pwd|pass)\s*[:=]\s*\S+", "[PASSWORD_REDACTED]", RegexOptions.IgnoreCase),
            new RedactionRule(@"\b(?:api[_-]?key|apikey)\s*[:=]\s*\S+", "[API_KEY_REDACTED]", RegexOptions.IgnoreCase),
            new RedactionRule(@"\b(?:token|auth[_-]?token)\s*[:=]\s*\S+", "[TOKEN_REDACTED]", RegexOptions.IgnoreCase),
            new RedactionRule(@"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP_ADDRESS_REDACTED]"),
            new RedactionRule(@"\b[A-Z][a-z]+ [A-Z][a-z]+\s*\([^)]*\)", "[NAME_REDACTED] (TITLE_REDACTED)"),
            new RedactionRule(@"\b[A-Z][a-z]+ [A-Z][a-z]+\b", "[NAME_REDACTED]")
        };
    }
}

// Represents a redaction rule (shared across all file types)
public class RedactionRule
{
    public string Pattern { get; }
    public string Replacement { get; }
    public RegexOptions Options { get; }

    public RedactionRule(string pattern, string replacement, RegexOptions options = RegexOptions.None)
    {
        Pattern = pattern;
        Replacement = replacement;
        Options = options;
    }
}
