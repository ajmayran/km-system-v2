from django.db import connection

# Define the SQL content directly
sql_content = """
-- Insert Commodities
INSERT INTO tbl_commodity (
    slug, commodity_name, description, resources_type, commodity_img, 
    date_created, date_edited, status, latitude, longitude
) VALUES 
('com001', 'Rice', 'Rice is the staple food of the Philippines, providing livelihood for millions of farmers.', 
 'Grains', NULL, '2024-01-01 00:00:00', NULL, 'active', 6.24420000, 124.24750000),

('com002', 'Coconut', 'Coconut is a major agricultural product in the Philippines, used for food, oil, and fiber.', 
 'Tree Crops', NULL, '2024-01-01 00:00:00', NULL, 'active', 6.52440000, 124.84520000),

('com003', 'Corn', 'Corn is widely cultivated in the Philippines as food and feed for livestock.', 
 'Grains', NULL, '2024-01-01 00:00:00', NULL, 'active', 6.11640000, 125.17160000),
clearckealcasd
('com004', 'Banana', 'Banana is one of the major fruit exports of the Philippines.', 
 'Fruits', NULL, '2024-01-01 00:00:00', NULL, 'active', 6.07110000, 125.61280000),

('com005', 'Sugarcane', 'Sugarcane is cultivated for sugar production in various regions of the Philippines.', 
 'Industrial Crops', NULL, '2024-01-01 00:00:00', NULL, 'active', 6.90950000, 122.07360000),

('com006', 'Mango', 'Philippine mango is known worldwide for its sweet taste and quality.', 
 'Fruits', NULL, '2024-01-01 00:00:00', NULL, 'active', 6.44140000, 124.63190000),

('com007', 'Pineapple', 'Pineapple is a major fruit crop in Mindanao, Philippines.', 
 'Fruits', NULL, '2024-01-01 00:00:00', NULL, 'active', 6.56440000, 124.84520000),

('com008', 'Coffee', 'Coffee production is growing in the mountainous regions of the Philippines.', 
 'Beverages', NULL, '2024-01-01 00:00:00', NULL, 'active', 6.24420000, 124.24750000),

('com009', 'Tilapia', 'Tilapia is widely cultured in freshwater systems across the Philippines.', 
 'Aquaculture', NULL, '2024-01-01 00:00:00', NULL, 'active', 6.11640000, 125.17160000),

('com010', 'Seaweed', 'Seaweed farming is a sustainable livelihood in coastal areas of the Philippines.', 
 'Marine Products', NULL, '2024-01-01 00:00:00', NULL, 'active', 6.90950000, 122.07360000);

-- Insert Knowledge Resources
INSERT INTO tbl_knowledge_resources (
    slug, knowledge_title, knowledge_description, machine_name, status, date_created
) VALUES 
('kr001', 'Agricultural Technologies', 'Latest technologies in agriculture including precision farming and smart irrigation systems.', 
 'agricultural_technologies', 'active', '2024-01-01 00:00:00'),

('kr002', 'Research Publications', 'Academic papers and research studies on agricultural innovations and best practices.', 
 'research_publications', 'active', '2024-01-01 00:00:00'),

('kr003', 'Training Materials', 'Educational resources and training modules for farmers and agricultural professionals.', 
 'training_materials', 'active', '2024-01-01 00:00:00'),

('kr004', 'Policy Documents', 'Government policies and regulations related to agriculture and rural development.', 
 'policy_documents', 'active', '2024-01-01 00:00:00'),

('kr005', 'Market Information', 'Market trends, prices, and trading information for agricultural commodities.', 
 'market_information', 'active', '2024-01-01 00:00:00'),

('kr006', 'Climate Data', 'Weather patterns, climate change impacts, and adaptation strategies for agriculture.', 
 'climate_data', 'active', '2024-01-01 00:00:00'),

('kr007', 'Extension Services', 'Agricultural extension programs and community outreach initiatives.', 
 'extension_services', 'active', '2024-01-01 00:00:00'),

('kr008', 'Sustainable Practices', 'Environmentally friendly farming methods and sustainable agricultural practices.', 
 'sustainable_practices', 'active', '2024-01-01 00:00:00');

-- Insert Tags
INSERT INTO tbl_knowledge_resources_tag (name, slug) VALUES 
('sustainable-agriculture', 'tag001'),
('precision-farming', 'tag002'),
('organic-farming', 'tag003'),
('climate-change', 'tag004'),
('food-security', 'tag005'),
('rural-development', 'tag006'),
('aquaculture', 'tag007'),
('livestock', 'tag008'),
('crop-protection', 'tag009'),
('irrigation', 'tag010'),
('soil-health', 'tag011'),
('pest-management', 'tag012'),
('harvesting', 'tag013'),
('post-harvest', 'tag014'),
('market-access', 'tag015'),
('technology-transfer', 'tag016'),
('research-development', 'tag017'),
('extension-services', 'tag018'),
('community-based', 'tag019'),
('innovation', 'tag020'),
('biotechnology', 'tag021'),
('genetics', 'tag022'),
('breeding', 'tag023'),
('nutrition', 'tag024'),
('processing', 'tag025'),
('value-adding', 'tag026'),
('export-quality', 'tag027'),
('certification', 'tag028');

-- Insert CMI Institutions
INSERT INTO tbl_cmi (
    slug, cmi_name, cmi_meaning, cmi_description, address, contact_num, email, 
    cmi_image, status, latitude, longitude, url, date_joined, date_created
) VALUES 
('cmi001', 'USP', 'University of Southern Philippines', 
 'Leading university in Southern Philippines focusing on agricultural research and development.',
 'Obrero, Davao City, Philippines', '+63 82 227 4637', 'info@usp.edu.ph', NULL, 'active',
 7.07310000, 125.61280000, 'https://www.usp.edu.ph', '2023-01-01', '2024-01-01'),

('cmi002', 'MSU', 'Mindanao State University',
 'Premier state university in Mindanao with strong agricultural programs.',
 'Marawi City, Lanao del Sur, Philippines', '+63 63 362 1004', 'info@msu.edu.ph', NULL, 'active',
 8.00420000, 124.29180000, 'https://www.msu.edu.ph', '2023-03-01', '2024-01-01'),

('cmi003', 'ADZU', 'Ateneo de Zamboanga University',
 'Jesuit university in Zamboanga with marine and agricultural research programs.',
 'La Purisima St, Zamboanga City, Philippines', '+63 62 991 0871', 'info@adzu.edu.ph', NULL, 'active',
 6.90950000, 122.07360000, 'https://www.adzu.edu.ph', '2023-06-01', '2024-01-01'),

('cmi004', 'CSU', 'Cotabato State University',
 'State university serving the SOCCSKSARGEN region with agricultural focus.',
 'Sinsuat Ave, Cotabato City, Philippines', '+63 64 421 3180', 'info@csu.edu.ph', NULL, 'active',
 7.22310000, 124.24520000, 'https://www.csu.edu.ph', '2023-08-01', '2024-01-01'),

('cmi005', 'DRC', 'Davao Research Center',
 'Research center specializing in tropical agriculture and sustainable farming.',
 'Davao City, Philippines', '+63 82 224 3456', 'info@drc.ph', NULL, 'active',
 7.19070000, 125.45530000, 'https://www.drc.ph', '2023-10-01', '2024-01-01');

-- Insert About Content
INSERT INTO tbl_about (content, date_created) VALUES 
('<h2>About AANR Knowledge Management Hub</h2>
<p>The AANR Knowledge Management Hub serves as the central repository for agricultural knowledge, research, and resources in the Philippines. Our mission is to promote sustainable agriculture through knowledge sharing, innovation, and collaboration among farmers, researchers, and agricultural professionals.</p>

<h3>Our Mission</h3>
<p>To accelerate agricultural development in the Philippines by providing accessible, reliable, and up-to-date agricultural information and technologies to farmers, researchers, and stakeholders.</p>

<h3>Our Vision</h3>
<p>A thriving agricultural sector powered by knowledge, innovation, and sustainable practices that ensures food security and rural prosperity for all Filipinos.</p>

<h3>Key Features</h3>
<ul>
    <li>Comprehensive agricultural knowledge repository</li>
    <li>Research publications and technical documents</li>
    <li>Training materials and educational resources</li>
    <li>Market information and price monitoring</li>
    <li>Technology transfer and innovation showcase</li>
    <li>Community forums and expert discussions</li>
</ul>

<h3>Partnership Network</h3>
<p>We collaborate with leading agricultural institutions, research centers, and universities across the Philippines to ensure our knowledge base remains current and relevant to the needs of our farming communities.</p>',
'2024-01-01 00:00:00');

-- Insert Useful Links
INSERT INTO tbl_useful_links (link_title, link, status, date_created) VALUES 
('Department of Agriculture', 'https://www.da.gov.ph', 'active', '2024-01-01'),
('Philippine Rice Research Institute', 'https://www.philrice.gov.ph', 'active', '2024-01-01'),
('Bureau of Fisheries and Aquatic Resources', 'https://www.bfar.da.gov.ph', 'active', '2024-01-01'),
('Agricultural Training Institute', 'https://www.ati.da.gov.ph', 'active', '2024-01-01'),
('National Irrigation Administration', 'https://www.nia.gov.ph', 'active', '2024-01-01'),
('Philippine Coconut Authority', 'https://www.pca.gov.ph', 'active', '2024-01-01'),
('Sugar Regulatory Administration', 'https://www.sra.gov.ph', 'active', '2024-01-01'),
('National Food Authority', 'https://www.nfa.gov.ph', 'active', '2024-01-01');


# Execute the SQL statements
cursor = connection.cursor()
statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

for i, statement in enumerate(statements):
    try:
        cursor.execute(statement)
        print(f"✅ Executed statement {i+1}")
    except Exception as e:
        print(f"❌ Error in statement {i+1}: {e}")

print("✅ Sample data loaded successfully!")