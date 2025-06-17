import os
from Bio import Entrez
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote

class PubMedService:
    def __init__(self):
        # Set your email for Entrez (required by NCBI)
        Entrez.email = os.getenv("PUBMED_EMAIL", "your_email@example.com")
        self.max_results = 3  # Limit results for performance
    
    def search_articles(self, query, max_results=None):
        """Search PubMed for articles related to the query"""
        if max_results is None:
            max_results = self.max_results
        
        try:
            # Search PubMed using Entrez
            search_handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=max_results,
                sort="relevance"
            )
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            id_list = search_results["IdList"]
            
            if not id_list:
                return {
                    "articles": [],
                    "message": "No relevant medical articles found for this query."
                }
            
            # Fetch article details in XML format for better parsing
            fetch_handle = Entrez.efetch(
                db="pubmed",
                id=id_list,
                rettype="abstract",
                retmode="xml"
            )
            articles_xml = fetch_handle.read()
            fetch_handle.close()
            
            # Parse and format the results
            formatted_results = self._parse_xml_results(articles_xml)
            return {
                "articles": formatted_results,
                "message": f"Found {len(formatted_results)} relevant articles"
            }
            
        except Exception as e:
            return {
                "articles": [],
                "error": f"Error searching PubMed: {str(e)}"
            }
    
    def _format_search_results(self, articles_text):
        """Format the search results into readable text"""
        if not articles_text:
            return "No articles found."
        
        # Split articles by record separator
        articles = articles_text.split('\n\n\n')
        formatted_articles = []
        
        for i, article in enumerate(articles[:self.max_results]):
            if article.strip():
                # Extract key information
                title = self._extract_field(article, "TI  - ")
                abstract = self._extract_field(article, "AB  - ")
                authors = self._extract_field(article, "AU  - ")
                journal = self._extract_field(article, "TA  - ")
                
                formatted_article = f"Article {i+1}:\n"
                if title:
                    formatted_article += f"Title: {title}\n"
                if authors:
                    formatted_article += f"Authors: {authors}\n"
                if journal:
                    formatted_article += f"Journal: {journal}\n"
                if abstract:
                    formatted_article += f"Abstract: {abstract[:300]}...\n"
                
                formatted_articles.append(formatted_article)
        
        return "\n---\n".join(formatted_articles) if formatted_articles else "No detailed information available."
    
    def _parse_xml_results(self, xml_data):
        """Parse XML results from PubMed and extract article information"""
        articles = []
        
        try:
            root = ET.fromstring(xml_data)
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    # Extract PMID
                    pmid_elem = article.find('.//PMID')
                    pmid = pmid_elem.text if pmid_elem is not None else None
                    
                    # Extract title
                    title_elem = article.find('.//ArticleTitle')
                    title = title_elem.text if title_elem is not None else "No title available"
                    
                    # Extract abstract
                    abstract_elem = article.find('.//AbstractText')
                    abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
                    
                    # Extract authors
                    authors = []
                    author_list = article.findall('.//Author')
                    for author in author_list[:3]:  # Limit to first 3 authors
                        lastname = author.find('LastName')
                        firstname = author.find('ForeName')
                        if lastname is not None and firstname is not None:
                            authors.append(f"{firstname.text} {lastname.text}")
                    
                    # Extract journal
                    journal_elem = article.find('.//Journal/Title')
                    journal = journal_elem.text if journal_elem is not None else "Unknown journal"
                    
                    # Extract publication date
                    year_elem = article.find('.//PubDate/Year')
                    year = year_elem.text if year_elem is not None else "Unknown year"
                    
                    articles.append({
                        'pmid': pmid,
                        'title': title,
                        'abstract': abstract[:500] + "..." if len(abstract) > 500 else abstract,
                        'authors': authors,
                        'journal': journal,
                        'year': year
                    })
                    
                except Exception as e:
                    continue  # Skip problematic articles
                    
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
            return []
            
        return articles

    def _extract_field(self, article_text, field_prefix):
        """Extract a specific field from article text"""
        lines = article_text.split('\n')
        field_content = []
        in_field = False
        
        for line in lines:
            if line.startswith(field_prefix):
                field_content.append(line[len(field_prefix):].strip())
                in_field = True
            elif in_field and line.startswith('      '):  # Continuation line
                field_content.append(line.strip())
            elif in_field and not line.startswith('      '):
                break
        
        return ' '.join(field_content) if field_content else None
    
    def get_article_summary(self, pmid):
        """Get summary of a specific article by PMID"""
        try:
            fetch_handle = Entrez.efetch(
                db="pubmed",
                id=pmid,
                rettype="abstract",
                retmode="text"
            )
            summary = fetch_handle.read()
            fetch_handle.close()
            return summary
        except Exception as e:
            return f"Error fetching article summary: {str(e)}"
    
    def search_related_terms(self, medical_term):
        """Search for articles related to specific medical terms"""
        # Enhanced query with medical subject headings (MeSH) terms
        enhanced_query = f'("{medical_term}"[MeSH Terms] OR "{medical_term}"[Title/Abstract])'
        return self.search_articles(enhanced_query)
