import wikipedia

def create_author_from_quote(quote_collection, people_collection):
     for quote_row in quote_collection.get_rows():
         author_name = quote_row.Author
    
         if author_name not in authors_seen:
             authors_seen.add(author_name)
             author_name, author_summary, author_image = get_wikipedia_data(author_name)
    
             people_row = people_collection.add_row(name=author_name)
             people_row.Description = author_summary
             people_row.Tags = ["Public Figure"]
             people_row.set("format.page_icon", "https://img.icons8.com/ios/250/000000/businessman.png")
             people_row.Quotes = [quote_row]

         else:
             continue

def get_wikipedia_data(author_name):
    print(f"Searching for {author_name}...")
    wiki_result = wikipedia.search(author_name)
    if len(wiki_result) > 0:
        pagename = wiki_result[0]
        author_name = pagename.split("(")[0].strip()
    
        print(f"Found as {author_name}!")
    
        summary = wikipedia.summary(pagename, sentences=2, auto_suggest=False)
    
        return author_name, summary, None
    
    return author_name, "", ""
