from django.db import connection

# Define the SQL content directly
sql_content = """
-- Insert Main About Entry
INSERT INTO tbl_about (
    about_id,
    project_name, 
    project_details,
    project_rationale_desc,
    date_created
) VALUES (
    1,
    'AANR Knowledge Hub',
    'A comprehensive platform for agricultural knowledge management and sharing.',
    'To provide a centralized system for managing and disseminating agricultural knowledge.',
    '2024-01-01 00:00:00'
);

-- Insert About Rationale
INSERT INTO tbl_about_rationale (
    rationale_id,
    about_id,
    title,
    detail
) VALUES (
    1,
    1,
    'Knowledge Management',
    'Facilitate effective sharing and management of agricultural knowledge resources.'
);

-- Insert About Objective
INSERT INTO tbl_about_objective (
    objective_id,
    about_id,
    title
) VALUES (
    1,
    1,
    'Centralized Knowledge Repository'
);

-- Insert About Objective Detail
INSERT INTO tbl_about_objective_detail (
    detail_id,
    objective_id,
    about_id,
    detail
) VALUES (
    1,
    1,
    1,
    'Create a unified platform for storing and accessing agricultural knowledge.'
);

-- Insert About Timeline
INSERT INTO tbl_about_timeline (
    timeline_id,
    about_id,
    title,
    description,
    date_start,
    date_end
) VALUES (
    1,
    1,
    'Project Initiation',
    'Launch of the AANR Knowledge Hub project.',
    '2024-01-01',
    '2024-12-31'
);

-- Insert Timeline Bullet
INSERT INTO tbl_timeline_bullets (
    id,
    timeline_id,
    details
) VALUES (
    1,
    1,
    'Project kickoff and team formation'
);

-- Insert Timeline Image
INSERT INTO tbl_timeline_images (
    id,
    timeline_id,
    image
) VALUES (
    1,
    1,
    NULL
);

-- Insert Team Member
INSERT INTO tbl_about_team_member (
    member_id,
    about_id,
    first_name,
    mid_name,
    last_name,
    role,
    description,
    email
) VALUES (
    1,
    1,
    'John',
    'M',
    'Doe',
    'Project Lead',
    'Expert in agricultural knowledge management systems',
    'john.doe@example.com'
);

-- Insert Team Social
INSERT INTO tbl_about_team_social (
    social_id,
    member_id,
    platform,
    link
) VALUES (
    1,
    1,
    'LinkedIn',
    'https://linkedin.com/in/johndoe'
);

-- Insert Sub Project
INSERT INTO tbl_about_sub_project (
    sub_id,
    about_id,
    project_name,
    project_details,
    project_rationale_desc,
    date_created
) VALUES (
    1,
    1,
    'Digital Library Module',
    'Electronic repository of agricultural publications and resources',
    'To provide easy access to digital agricultural resources',
    '2024-01-01 00:00:00'
);

-- Insert Sub Project Rationale
INSERT INTO tbl_about_rationale_sub_project (
    rationale_id,
    about_id,
    title,
    detail
) VALUES (
    1,
    1,
    'Digital Access',
    'Improve accessibility of agricultural resources through digital means'
);

-- Insert Sub Project Objective
INSERT INTO tbl_about_objective_sub_project (
    objective_id,
    about_id,
    title
) VALUES (
    1,
    1,
    'Resource Digitization'
);

-- Insert Sub Project Objective Detail
INSERT INTO tbl_about_objective_detail_sub_project (
    detail_id,
    objective_id,
    about_id,
    detail
) VALUES (
    1,
    1,
    1,
    'Convert physical resources into digital format for easy access'
);

-- Insert Sub Project Timeline
INSERT INTO tbl_about_timeline_sub_project (
    timeline_id,
    about_id,
    title,
    description,
    date_start,
    date_end
) VALUES (
    1,
    1,
    'Module Development',
    'Development phase of the digital library module',
    '2024-01-01',
    '2024-06-30'
);

-- Insert Sub Project Timeline Bullet
INSERT INTO tbl_timeline_bullets_sub_project (
    id,
    timeline_id,
    details
) VALUES (
    1,
    1,
    'Initial system architecture design'
);

-- Insert Sub Project Timeline Image
INSERT INTO tbl_timeline_images_sub_project (
    id,
    timeline_id,
    image
) VALUES (
    1,
    1,
    NULL
);

-- Insert Sub Project Team Member
INSERT INTO tbl_about_team_member_sub_project (
    member_id,
    about_id,
    first_name,
    mid_name,
    last_name,
    role,
    description,
    email
) VALUES (
    1,
    1,
    'Jane',
    'A',
    'Smith',
    'Module Lead',
    'Digital library systems specialist',
    'jane.smith@example.com'
);

-- Insert Sub Project Team Social
INSERT INTO tbl_about_team_social_sub_project (
    social_id,
    member_id,
    platform,
    link
) VALUES (
    1,
    1,
    'LinkedIn',
    'https://linkedin.com/in/janesmith'
);
"""

# Execute the SQL statements
cursor = connection.cursor()
statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

for i, statement in enumerate(statements):
    try:
        cursor.execute(statement)
        print(f"✅ Executed statement {i+1}")
    except Exception as e:
        print(f"❌ Error in statement {i+1}: {e}")

print("✅ Sample about data loaded successfully!")