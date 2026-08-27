from pathlib import Path
from statistics import mean
import os

import chromadb
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


REBUILD = False
PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "it_companies"
CORPUS_DIR = Path("data/company_profiles")

PROFILES = {
    "tcs.txt": ("Tata Consultancy Services", "TCS", """Tata Consultancy Services, commonly called TCS, was founded in 1968 and is headquartered in Mumbai. It is part of the Tata Group and has grown into India's largest IT services exporter. K Krithivasan became chief executive officer in June 2023. The company employs approximately 600,000 people across a broad international delivery network.

TCS helps organizations modernize applications, manage infrastructure, build cloud platforms, and use data and artificial intelligence responsibly. Its work spans banking, insurance, retail, manufacturing, telecommunications, healthcare, travel, and the public sector. A large distributed delivery model combines Indian engineering centers with client-facing teams in North America, Europe, Asia Pacific, and other regions.

The company is known for long-running relationships with large enterprises and for combining consulting with implementation and managed services. Teams commonly support enterprise resource planning, cybersecurity, quality engineering, customer experience, and business process operations. These service lines allow a customer to move from strategy through production support with one primary technology partner.

TCS invests in training, internal learning platforms, and partnerships with universities and technology providers. Its innovation programs explore cloud-native architecture, automation, generative AI, and industry-specific software. The company generally presents these capabilities as tools for measurable productivity, resilience, and improved customer service rather than as substitutes for responsible governance.

Customer programs are usually measured through delivery quality, business continuity, modernization milestones, and the ability to change services as needs evolve. Account teams coordinate architects, delivery leaders, security specialists, and domain experts. This operating discipline is one reason the company can support both large transformation programs and ongoing technology operations for complex enterprises.

The breadth of its customer base gives TCS experience with both shared technology patterns and specialized industry requirements. Teams document decisions, monitor service performance, and use feedback from operations to improve future releases. This keeps the profile's emphasis on durable delivery practices rather than on temporary product announcements.

Its delivery centers operate with common processes while adapting to local regulation and language needs. This scale supports follow-the-sun operations and continuity for global customers. Project teams are organized around business outcomes, engineering disciplines, and domain knowledge, with security and privacy controls built into delivery practices.

Sustainability is part of the company's operational agenda. Programs address energy use in offices and data centers, renewable power, efficient facilities, responsible supply chains, and community education. TCS also supports employability and digital literacy initiatives through the wider Tata Group ecosystem.

The profile describes a large services enterprise rather than a live market data feed. Its historical facts and leadership information are intended for training retrieval systems. Financial market values, stock prices, share-price history, sports results, and FIFA World Cup information are deliberately outside this profile and should not be inferred from it.

In summary, TCS combines a very large workforce, a global delivery footprint, and a wide portfolio of consulting and technology services. Its Tata Group identity, Mumbai headquarters, 1968 founding year, and leadership under K Krithivasan are useful distinguishing facts for comparing Indian IT companies."""),
    "infosys.txt": ("Infosys", "Infosys", """Infosys was founded in 1981 in Pune, and its headquarters are now in Bengaluru. The company was co-founded by N. R. Narayana Murthy and six others. Salil Parekh is the chief executive officer. For FY2025, Infosys provided revenue growth guidance of 3-4% in constant currency, a business detail that should be read in its stated fiscal-year context.

The company provides consulting, technology implementation, application management, cloud services, cybersecurity, data and analytics, and business process services. Its customers operate in financial services, retail, communications, manufacturing, healthcare, energy, and other industries. Infosys often positions transformation programs around modernization, digital operating models, and efficient use of enterprise technology.

Infosys maintains delivery and innovation locations in India and around the world. Distributed teams work with customers in North America, Europe, Asia Pacific, and other markets. The operating model combines domain consultants, software engineers, experience specialists, and program leaders so that large projects can be designed, built, and supported over time.

Cloud adoption, automation, artificial intelligence, and responsible data use are recurring themes in the company's technology work. Its learning culture emphasizes continuous skills development and professional certifications. Partnerships with major cloud and software providers extend the range of platforms available to customers without changing the company's role as an implementation and services partner.

Project teams commonly begin with a customer's existing systems, processes, and controls before recommending a target state. This approach helps connect investment decisions to measurable business outcomes and makes change easier to govern. It also gives specialists in architecture, engineering, operations, and organizational change a shared view of the work.

Infosys engagements may include discovery, roadmap planning, implementation, transition, and continuing support. Clear ownership and regular measurement help customers understand what changed and whether the change delivered value. The same discipline applies when work is delivered from several locations and must meet different local obligations.

The organization has also developed products, platforms, and industry solutions that package repeatable capabilities for common enterprise needs. These offerings can support finance operations, customer service, supply chain processes, and employee experience. Consulting engagements typically connect those capabilities to a customer's existing architecture, controls, and change-management plan.

Environmental and social programs include energy efficiency, renewable electricity, water stewardship, inclusion, employee volunteering, and education initiatives. The company reports on operational responsibility as part of its broader governance approach. Local teams may tailor community programs to the needs of the regions where employees and customers are based.

This is a stable training profile with facts as of FY2025, not a live company-information service. It intentionally contains no stock price, share-price history, market capitalization, sports result, cricket result, or FIFA World Cup result. Questions about those subjects should be treated as unanswered by this corpus.

Infosys can be distinguished by its 1981 Pune origin, present Bengaluru headquarters, founding team that included N. R. Narayana Murthy and six others, leadership by Salil Parekh, and FY2025 constant-currency growth guidance of 3-4%. Those facts make it useful for single-company and multi-hop retrieval exercises."""),
    "wipro.txt": ("Wipro", "Wipro", """Wipro was founded in 1945 as Western India Vegetable Products and later pivoted to information technology in the 1980s. It is headquartered in Bengaluru. Srini Pallia was appointed chief executive officer in 2024. Wipro serves clients in 66 countries through a global network of delivery centers and customer teams.

The company works across consulting, applications, cloud, infrastructure, cybersecurity, engineering, data, and business process services. Its industry coverage includes banking, healthcare, consumer products, communications, energy, manufacturing, and public services. Engagements range from targeted modernization projects to long-term managed operations with distributed support teams.

Wipro's technology work often connects business process redesign with cloud adoption and software engineering. Automation, analytics, artificial intelligence, and platform integration are used to improve reliability and customer experience. Teams are expected to balance speed with controls for security, privacy, compliance, and operational resilience.

Delivery planning typically considers the customer's existing estate, the desired operating model, and the skills required after transition. Architects and service leaders work with business stakeholders to sequence modernization so that important operations remain stable. Measurement can include service quality, automation, resilience, and customer experience improvements.

Wipro's teams also help customers establish repeatable controls around releases, incidents, access, and data. Those controls matter when a service crosses several vendors or regions. A practical operating model can make modernization easier to sustain after the initial consulting and implementation work is complete.

Its international presence helps the company support customers across time zones and regulatory environments. Indian delivery centers provide engineering and operations capacity while regional teams contribute local market knowledge and executive relationships. The combination is intended to give customers consistent methods with practical local accountability.

The company invests in talent development through technical academies, role-based learning, and professional certifications. It also works with technology partners and ecosystem organizations to broaden its cloud, enterprise application, and data capabilities. These efforts support employees as customer technology estates become more distributed and software-led.

Sustainability activity includes reducing operational emissions, improving energy efficiency, encouraging responsible procurement, and supporting social programs. Community initiatives may focus on education, health, employability, and digital access. Governance and reporting practices are used to track commitments and provide visibility to stakeholders.

This profile is a deliberately bounded training document with facts as of FY2025. It does not provide stock prices, historical share prices, market capitalization, sports information, cricket information, or FIFA World Cup results. A retrieval system should refuse questions that require any of those missing facts rather than filling the gap from general knowledge.

Wipro's historical path from vegetable products to information technology, Bengaluru headquarters, leadership by Srini Pallia from 2024, and service to clients in 66 countries give it a distinct identity in comparisons among Indian IT services companies. The 1945 founding year also makes it an important candidate in earliest-founded-company queries."""),
    "hcltech.txt": ("HCLTech", "HCLTech", """HCLTech was founded in 1976 and is headquartered in Noida. C Vijayakumar is the chief executive officer. The company has a strong engineering-and-R&D services mix, supporting organizations that design, build, modernize, and operate technology products and enterprise systems.

Its services include digital engineering, product development, cloud transformation, applications, infrastructure, cybersecurity, data, and artificial intelligence. HCLTech works with clients in technology, financial services, manufacturing, healthcare, life sciences, telecommunications, media, retail, and public services. The combination of engineering depth and managed services helps customers connect product goals with dependable operations.

Engineering teams may contribute to embedded systems, semiconductor programs, software platforms, user experiences, testing, and product lifecycle management. Enterprise teams support application modernization, infrastructure transformation, workplace services, and business process improvement. Programs are typically shaped around a client's architecture, controls, and industry obligations.

The engineering approach links discovery, design, development, testing, and operations across the product lifecycle. Specialists may work alongside a customer's product organization or take responsibility for defined platforms and services. Clear interfaces, quality gates, and security reviews help teams deliver changes without losing sight of reliability.

HCLTech therefore occupies a useful position between product engineering and enterprise operations. Its teams can focus on a discrete component, a complete platform, or a broader transformation program. In each case, technical quality, documentation, and dependable handover are important parts of the delivery model.

HCLTech operates through delivery centers and customer-facing offices across India and international markets. Global teams collaborate across time zones and bring local knowledge to regulated industries. Standard engineering methods, quality practices, and security reviews are used to make work repeatable while allowing teams to adapt to product and customer requirements.

The company emphasizes learning in cloud platforms, software engineering, data, cyber defense, and industry domains. Ecosystem relationships with major technology providers extend its implementation options. Innovation work commonly focuses on practical modernization, automation, intelligent operations, and the dependable use of emerging technology.

Responsible operations include attention to energy and emissions, resource efficiency, inclusion, employee development, and community programs. HCLTech's social initiatives may support education, health, digital skills, and local resilience. Governance processes help connect these activities with business risk management and customer expectations.

This document is a training corpus profile with facts as of FY2025, not a source for live market information. It intentionally omits stock prices, share-price history, market capitalization, sports, cricket, and FIFA World Cup facts. Missing information should remain an explicit retrieval limitation.

HCLTech is particularly useful in this exercise because its 1976 founding year, Noida headquarters, leadership by C Vijayakumar, and strong engineering-and-R&D services mix contrast with the other companies. Those facts support both direct questions and comparisons of service orientation."""),
    "tech_mahindra.txt": ("Tech Mahindra", "TechMahindra", """Tech Mahindra was founded in 1986 and is headquartered in Pune. It is part of the Mahindra Group. Mohit Joshi became chief executive officer in December 2023. The company has a telecom-heavy client base and serves communications providers as well as customers in many other industries.

Its capabilities include network services, engineering, cloud, applications, cybersecurity, customer experience, data, and business process services. Telecom programs can involve network transformation, operations support, 5G-related platforms, service assurance, and customer care. Work in manufacturing, financial services, healthcare, retail, and technology broadens the company's delivery portfolio beyond communications.

Tech Mahindra combines consulting and engineering with implementation and managed services. Teams help customers modernize legacy estates, automate service operations, improve digital channels, and connect data across complex organizations. Delivery decisions account for reliability, security, privacy, and the operational demands of always-on communications environments.

Programs often begin by mapping customer journeys, network dependencies, applications, and operational controls. This creates a practical basis for prioritizing improvements and managing transition risk. Engineering, service management, and business teams can then track outcomes such as faster issue resolution, simpler operations, and more dependable digital experiences.

The communications background also makes service continuity especially important. Teams consider capacity, incident response, observability, and customer communication when planning changes. These concerns complement the company's broader consulting and engineering capabilities and explain why telecom remains a central context for its work.

The company uses delivery centers in India and international locations, with customer-facing specialists close to important markets. Distributed collaboration supports global programs while domain experts contribute knowledge of network architecture, enterprise systems, and industry processes. Regional teams also help customers navigate local regulatory and language requirements.

Learning programs develop skills in cloud, software engineering, network technologies, artificial intelligence, analytics, and service management. Partnerships across the technology ecosystem expand available platforms and specialist capabilities. Innovation efforts are generally tied to practical customer outcomes such as faster provisioning, better service quality, and more efficient operations.

Environmental and social priorities include energy management, emissions reduction, inclusion, workforce development, and community investment. Programs may support education, employability, digital access, and local communities. Reporting and governance practices provide a framework for measuring progress and managing operational responsibility.

This is a bounded training profile with facts as of FY2025. It contains no stock price, share-price history, market capitalization, sports, cricket, or FIFA World Cup information. A question about one of those subjects cannot be answered from this document collection.

Tech Mahindra's Pune headquarters, Mahindra Group membership, 1986 founding year, leadership by Mohit Joshi from December 2023, and telecom-heavy client base distinguish it from the other profiles. These details make it useful for company-membership, headquarters, and multi-hop retrieval questions."""),
}


def require_api_key():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is missing. Copy .env.example to .env and add your key.")


def build_corpus():
    if CORPUS_DIR.exists():
        return 0
    CORPUS_DIR.mkdir(parents=True)
    for filename, (company_name, _, body) in PROFILES.items():
        text = f"# {company_name} — company profile (training corpus, facts as of FY2025)\n\n{body}\n"
        (CORPUS_DIR / filename).write_text(text, encoding="utf-8")
    return len(PROFILES)


def load_documents():
    company_map = {filename: code for filename, (_, code, _) in PROFILES.items()}
    documents = []
    for path in sorted(CORPUS_DIR.glob("*.txt")):
        document = TextLoader(str(path), encoding="utf-8").load()[0]
        document.metadata.update(company=company_map.get(path.name, path.stem), source=path.name, doc_type="profile")
        documents.append(document)
    return documents


def print_results(vectorstore, queries):
    all_results = []
    for index, (query, query_type) in enumerate(queries, 1):
        results = vectorstore.similarity_search_with_relevance_scores(query, k=5)
        all_results.append(results)
        print(f"\n[Q{index}] {query} ({query_type})")
        for rank, (document, score) in enumerate(results, 1):
            preview = " ".join(document.page_content.split())[:70]
            print(f"  {rank}. {score:.3f}  {document.metadata.get('company', '?'):<12} {document.metadata.get('source', '?'):<20} {preview}...")
        companies = sorted({doc.metadata.get("company", "?") for doc, _ in results})
        scores = [score for _, score in results]
        print(f"  -> top score {max(scores, default=0):.3f} | mean top-5 {mean(scores) if scores else 0:.3f} | distinct companies: {', '.join(companies) or 'none'}")
        if index == 3:
            print(f"  -> multi-hop coverage TCS + Infosys: {'PASS' if {'TCS', 'Infosys'} <= set(companies) else 'MISS'}")
        if index == 4:
            print(f"  -> multi-hop coverage includes Wipro: {'PASS' if 'Wipro' in companies else 'MISS'}")
    return all_results


def main():
    require_api_key()
    written = build_corpus()
    print(f"Corpus files written: {written}; profile files present: {len(list(CORPUS_DIR.glob('*.txt')))}")
    documents = load_documents()
    print(f"Documents loaded: {len(documents)}; total characters: {sum(len(doc.page_content) for doc in documents)}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50, separators=["\n\n", "\n", ". ", " ", ""])
    # chunk_size counts characters, not tokens: the default length_function is len.
    chunks = splitter.split_documents(documents)
    lengths = [len(chunk.page_content) for chunk in chunks]
    counts = {code: sum(chunk.metadata["company"] == code for chunk in chunks) for code in sorted({chunk.metadata["company"] for chunk in chunks})}
    print(f"Chunks: {len(chunks)}; per company: {counts}; min/mean/max length: {min(lengths)}/{mean(lengths):.1f}/{max(lengths)}")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    existing = next((item for item in client.list_collections() if getattr(item, "name", item) == COLLECTION_NAME), None)
    if REBUILD and existing:
        client.delete_collection(COLLECTION_NAME)
    vectorstore = Chroma(collection_name=COLLECTION_NAME, persist_directory=PERSIST_DIR, embedding_function=embeddings, collection_metadata={"hnsw:space": "cosine"})
    if vectorstore._collection.count() == 0:
        ids = [f"{chunk.metadata['company']}_{index:03d}" for index, chunk in enumerate(chunks)]
        vectorstore.add_documents(chunks, ids=ids)
    count = vectorstore._collection.count()
    print(f"Collection {COLLECTION_NAME} count after indexing: {count}")
    assert count == len(chunks), "Collection count does not match chunk count; use REBUILD = True."

    queries = [("Who is the CEO of TCS and when was the company founded?", "in-domain"), ("What is Infosys revenue growth guidance for FY2025?", "in-domain"), ("Compare the founding years of TCS and Infosys", "multi-hop"), ("Which Indian IT company was founded earliest?", "multi-hop"), ("Who won the FIFA World Cup in 2022?", "out-of-domain")]
    print_results(vectorstore, queries)
    threshold_counts = {}
    print("\nTHRESHOLD SWEEP (surviving chunks)")
    print("threshold | " + " | ".join(f"Q{i}" for i in range(1, 6)))
    for threshold in [0.4, 0.6, 0.7, 0.8]:
        retriever = vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": threshold, "k": 5})
        values = [len(retriever.invoke(query)) for query, _ in queries]
        threshold_counts[threshold] = values
        print(f"{threshold:9.1f} | " + " | ".join(f"{value:2d}" for value in values))
    q5_zero = next((threshold for threshold, values in threshold_counts.items() if values[4] == 0), "never")
    print(f"\nInterpretation: Q5 returns {threshold_counts[0.4][4]} chunks at 0.4 and {threshold_counts[0.8][4]} at 0.8; it first returns zero at {q5_zero}.")
    print(f"\nSummary: {len(chunks)} chunks in {COLLECTION_NAME} at {PERSIST_DIR}; out-of-domain empty threshold: {q5_zero}.")
    print("Labs 2 and 3 will reuse ./chroma_db.")


if __name__ == "__main__":
    main()