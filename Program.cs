using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using System.Text;

// See https://aka.ms/new-console-template for more information

try
{
    // Read the DOCX file and store its content in a variable
    string docxFilePath = "docs/1.docx";
    string documentContent = ReadDocxContent(docxFilePath);
    
    Console.WriteLine("Document content loaded successfully!");
    Console.WriteLine($"Content length: {documentContent.Length} characters");
    Console.WriteLine("\n--- Document Content ---");
    Console.WriteLine(documentContent);
}
catch (Exception ex)
{
    Console.WriteLine($"Error reading the DOCX file: {ex.Message}");
}

static string ReadDocxContent(string filePath)
{
    StringBuilder content = new StringBuilder();
    
    using (WordprocessingDocument wordDoc = WordprocessingDocument.Open(filePath, false))
    {
        Body? body = wordDoc.MainDocumentPart?.Document?.Body;
        if (body != null)
        {
            foreach (var paragraph in body.Elements<Paragraph>())
            {
                foreach (var run in paragraph.Elements<Run>())
                {
                    foreach (var text in run.Elements<Text>())
                    {
                        content.Append(text.Text);
                    }
                }
                content.AppendLine(); // Add line break after each paragraph
            }
        }
    }
    
    return content.ToString();
}
