from atPaceAI import best_matches

# Sample data for mentor and mentee profiles
data_mentee = [{
    "ID": "b27ba9c0-3636-40af-bddd-296c18911077",
    "Email": "wafiq.dawood@gmail.com",
    "Name": "Wafiq Dawood",
    "Profession": "Mentee",
    "Interested Topic": "AI, ML, web dev",
    "responses": ["Other Industry I want to explore more about working overseas,  assessing how the global workforce situation is and learning about different working cultures abroad.",
                  ". Learn what differences can potentially cause conflict and how to avoid them.",
                  "Build more connections. Malay Jena I'm very open to working overseas and always look for new opportunities for growth. "]
}]

data_mentee_complete = [{
    "ID": "b27ba9c0-3636-40af-bddd-296c18911077",
    "Name": "Wafiq Dawood",
    "Email": "wafiq.dawood@gmail.com",
    "Profession": "Mentee",
    "Interested Topic": "AI, ML, web dev",
    "responses": ["Other Industry I want to explore more about working overseas,  assessing how the global workforce situation is and learning about different working cultures abroad.",
                  ". Learn what differences can potentially cause conflict and how to avoid them.",
                  "Build more connections. Malay Jena I'm very open to working overseas and always look for new opportunities for growth. "],
    "Summary": "Malay Jena wants to explore more about working overseas, assessing how the global workforce situation is and learning about different working cultures abroad . I'm very open to working overseas and always look for new opportunities for growth . Learn what differences can potentially cause conflict and how to avoid them ."
}]

data_mentor = [{
    "ID": "b27ba9c0-3636-40af-bddd-296c18772",
    "Email": "shukla.prashant@gmail.com",
    "Name": "Prashant Shukla",
    "Profession": "Mentor",
    "Expertize": "Content writing, HR, finance, tax, management, leadership",
    "responses": ["https://www.linkedin.com/in/prashant-shukla-06912555 prashant shukla HRS Associate- Reward and Payroll Operations Data analytics,",
                  ", Policy analysis, root cause analysis HRS associate Senior level Understand the requirements and skills required for new to career population, provide technical expertise and ideas to up skill Human Resources Compensation, benefits, global mobility Equinix",
                  "Compensation and benefits, HR operations Edinburgh, UK Modern Services (Professional and Consultancy Services, Information & Communications Technology, Media & Financial Services) ",
                  "Banking Yes Mentor for student community at Enactus - an entrepreneurial venture for students No Special compensation measures, expat benefits and EMEA benefits "]
},

{
    "ID": "8ec82456-fc4a-4b84-9f28-d00a74255a20",
    "Email": "marz14790@gmail.com",
    "Name": "Marz Dawa",
    "Profession": "Mentor",
    "Expertize": "Python and AI, Deep learning, ML, artificial intelligence, web development",
    "responses": ["https://www.linkedin.com/in/mariam-verghese-06912555 Mariam associate working in Cognizant as senior machine learning engineer",
                  ", Policy analysis, root cause analysis HRS associate Senior level Understand the requirements and skills required for new to career population, provide technical expertise and ideas to up skill Data science, machine learning, AI, programming, system design",
                  "Compensation and benefits, DS operations Edinburgh, UK Modern Services (Professional and Consultancy Services, Information & technology",
                  "host events related to tech and programming "]
},
    {
        "ID": "mentor_id_0",
        "Email": "mentor0@example.com",
        "Name": "Mentor 0",
        "Profession": "Mentor",
        "Expertize": ["Software Engineering", "Web Development", "Cloud Computing", "Data Analysis"],
        "responses": [
            "https://www.linkedin.com/in/mentor0 Mentor 0's LinkedIn Profile",
            "Mentor 0 is a software engineer with expertise in web development, cloud computing, and data analysis.",
            "In the past, Mentor 0 has worked on various web development projects, including e-commerce websites and web applications.",
            "Mentor 0 is highly skilled in cloud computing technologies such as AWS and Azure and has experience in managing large-scale cloud infrastructures.",
            "Data analysis is one of Mentor 0's core strengths, and they have worked extensively with data visualization tools and statistical analysis.",
            "Mentor 0 is excited to share their knowledge and experiences with aspiring developers and data analysts."
        ]
    },
    {
        "ID": "mentor_id_1",
        "Email": "mentor1@example.com",
        "Name": "Mentor 1",
        "Profession": "Mentor",
        "Expertize": ["Marketing", "Social Media Management", "Branding", "Market Research"],
        "responses": [
            "https://www.linkedin.com/in/mentor1 Mentor 1's LinkedIn Profile",
            "Mentor 1 is a marketing expert with a focus on social media management, branding, and market research.",
            "They have successfully managed social media campaigns for various brands, resulting in increased brand visibility and engagement.",
            "Mentor 1 has a keen eye for branding and has helped businesses establish their unique brand identity.",
            "Market research is one of Mentor 1's strengths, and they have conducted in-depth analysis to identify market trends and opportunities.",
            "As a mentor, they are passionate about helping marketing enthusiasts gain valuable skills and insights."
        ]
    },
    {
        "ID": "mentor_id_9",
        "Email": "mentor9@example.com",
        "Name": "Mentor 9",
        "Profession": "Mentor",
        "Expertize": ["Product Management", "Product Development", "Product Strategy", "Market Analysis"],
        "responses": [
            "https://www.linkedin.com/in/mentor9 Mentor 9's LinkedIn Profile",
            "Mentor 9 is an experienced product manager with a strong background in product development and strategy.",
            "They have successfully launched several products in the market and have a deep understanding of market analysis and customer needs.",
            "Mentor 9's expertise lies in defining product roadmaps, conducting market research, and driving product innovation.",
            "In the past, Mentor 9 has collaborated with cross-functional teams to deliver products that meet customer requirements and drive business growth.",
            "As a mentor, they are committed to guiding aspiring product managers and helping them excel in their roles."
        ]
    }
]

data_mentor_complete = [{
    "ID": "b27ba9c0-3636-40af-bddd-296c18772",
    "Email": "shukla.prashant@gmail.com",
    "Name": "Prashant Shukla",
    "Profession": "Mentor",
    "Expertize": "Content writing, HR, finance, tax, management, leadership",
    "responses": ["https://www.linkedin.com/in/prashant-shukla-06912555 prashant shukla HRS Associate- Reward and Payroll Operations Data analytics,",
                  ", Policy analysis, root cause analysis HRS associate Senior level Understand the requirements and skills required for new to career population, provide technical expertise and ideas to up skill Human Resources Compensation, benefits, global mobility Equinix",
                  "Compensation and benefits, HR operations Edinburgh, UK Modern Services (Professional and Consultancy Services, Information & Communications Technology, Media & Financial Services) ",
                  "Banking Yes Mentor for student community at Enactus - an entrepreneurial venture for students No Special compensation measures, expat benefits and EMEA benefits "],
    "Summary": "HRS Associate- Reward and Payroll Operations Data analytics,., Policy analysis, root cause analysis . Understand the requirements and skills required for new to career population, provide technical expertise and ideas to up skill . Mentor for student community at Enactus - an entrepreneurial venture for students ."
},

{
    "ID": "8ec82456-fc4a-4b84-9f28-d00a74255a20",
    "Email": "marz14790@gmail.com",
    "Name": "Marz Dawa",
    "Profession": "Mentor",
    "Expertize": "Python and AI, Deep learning, ML, artificial intelligence, web development",
    "responses": ["https://www.linkedin.com/in/mariam-verghese-06912555 Mariam associate working in Cognizant as senior machine learning engineer",
                  ", Policy analysis, root cause analysis HRS associate Senior level Understand the requirements and skills required for new to career population, provide technical expertise and ideas to up skill Data science, machine learning, AI, programming, system design",
                  "Compensation and benefits, DS operations Edinburgh, UK Modern Services (Professional and Consultancy Services, Information & technology",
                  "host events related to tech and programming "],
    "Summary": " Mariam associate working in Cognizant as senior machine learning engineer . Policy analysis, root cause analysis and policy analysis . Understand the requirements and skills required for new to career population, provide technical expertise and ideas to up skill Data science, machine learning, AI, programming, system design."
},
    {
        "ID": "mentor_id_0",
        "Email": "mentor0@example.com",
        "Name": "Mentor 0",
        "Profession": "Mentor",
        "Expertize": ["Software Engineering", "Web Development", "Cloud Computing", "Data Analysis"],
        "responses": [
            "https://www.linkedin.com/in/mentor0 Mentor 0's LinkedIn Profile",
            "Mentor 0 is a software engineer with expertise in web development, cloud computing, and data analysis.",
            "In the past, Mentor 0 has worked on various web development projects, including e-commerce websites and web applications.",
            "Mentor 0 is highly skilled in cloud computing technologies such as AWS and Azure and has experience in managing large-scale cloud infrastructures.",
            "Data analysis is one of Mentor 0's core strengths, and they have worked extensively with data visualization tools and statistical analysis.",
            "Mentor 0 is excited to share their knowledge and experiences with aspiring developers and data analysts."
        ],
        "Summary": "Mentor 0 is a software engineer with expertise in web development, cloud computing, and data analysis . The company is highly skilled in cloud computing technologies such as AWS and Azure and has experience in managing large-scale cloud infrastructures . The team is excited to share their knowledge and experiences with aspiring developers and data analysts ."
    },
    {
        "ID": "mentor_id_1",
        "Email": "mentor1@example.com",
        "Name": "Mentor 1",
        "Profession": "Mentor",
        "Expertize": ["Marketing", "Social Media Management", "Branding", "Market Research"],
        "responses": [
            "https://www.linkedin.com/in/mentor1 Mentor 1's LinkedIn Profile",
            "Mentor 1 is a marketing expert with a focus on social media management, branding, and market research.",
            "They have successfully managed social media campaigns for various brands, resulting in increased brand visibility and engagement.",
            "Mentor 1 has a keen eye for branding and has helped businesses establish their unique brand identity.",
            "Market research is one of Mentor 1's strengths, and they have conducted in-depth analysis to identify market trends and opportunities.",
            "As a mentor, they are passionate about helping marketing enthusiasts gain valuable skills and insights."
        ],
        "Summary": "Mentor 1 is a marketing expert with a focus on social media management, branding, and market research . They have successfully managed social media campaigns for various brands, resulting in increased brand visibility and engagement . As a mentor, they are passionate about helping marketing enthusiasts gain valuable skills and insights ."
    },
    {
        "ID": "mentor_id_9",
        "Email": "mentor9@example.com",
        "Name" : "Mentor 9",
        "Profession": "Mentor",
        "Expertize": ["Product Management", "Product Development", "Product Strategy", "Market Analysis"],
        "responses": [
            "https://www.linkedin.com/in/mentor9 Mentor 9's LinkedIn Profile",
            "Mentor 9 is an experienced product manager with a strong background in product development and strategy.",
            "They have successfully launched several products in the market and have a deep understanding of market analysis and customer needs.",
            "Mentor 9's expertise lies in defining product roadmaps, conducting market research, and driving product innovation.",
            "In the past, Mentor 9 has collaborated with cross-functional teams to deliver products that meet customer requirements and drive business growth.",
            "As a mentor, they are committed to guiding aspiring product managers and helping them excel in their roles."
        ],
        "Summary": "Mentor 9 is an experienced product manager with a strong background in product development and strategy . They have successfully launched several products in the market and have a deep understanding of market analysis and customer needs . As a mentor, they are committed to guiding aspiring product managers and helping them excel in their roles ."
    }
]

result = best_matches(mentees=data_mentee, mentors=data_mentor, num_top_mentors=2)
print(result)