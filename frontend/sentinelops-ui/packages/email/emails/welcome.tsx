import {
  Body,
  Button,
  Container,
  Heading,
  Hr,
  Html,
  Img,
  Link,
  Preview,
  Section,
  Tailwind,
} from "@react-email/components";
import { Logo } from "components/logo";

const baseUrl = process.env.VERCEL_URL
  ? `https://${process.env.VERCEL_URL}`
  : "http://localhost:3001";

export default function WelcomeEmail() {
  return (
    <Html>
      <Preview>Welcome to SentinelOps</Preview>
      <Tailwind>
        <Body className="my-auto mx-auto font-sans">
          <Container className="border-transparent my-[40px] mx-auto max-w-[600px]">
            <Logo baseUrl={baseUrl} />
            <Heading className="font-normal text-center p-0 my-[30px] mx-0">
              Welcome to SentinelOps
            </Heading>
            <Section className="mb-4">
              Hi, welcome to SentinelOps - your intelligent cybersecurity operations platform.
            </Section>
            <Section className="mb-4">
              SentinelOps provides autonomous threat detection, response, and 
              security orchestration powered by advanced AI agents. Our platform 
              helps security teams stay ahead of evolving threats with real-time 
              monitoring and automated incident response.
            </Section>
            <Section className="mb-4">
              Get started with our interactive dashboard to monitor your security 
              posture, configure automated responses, and view real-time threat 
              intelligence from across your infrastructure.
            </Section>
            <Section className="mb-8">
              Our AI-powered agents continuously learn from your environment to 
              provide better protection and reduce false positives while ensuring 
              comprehensive security coverage.
            </Section>
            <Section className="mb-6">
              <Link href={baseUrl}>
                <Button className="bg-black text-white p-4 text-center">
                  Access Dashboard
                </Button>
              </Link>
            </Section>
            <Hr />
          </Container>
        </Body>
      </Tailwind>
    </Html>
  );
}
