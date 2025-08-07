'use client'
import LivestreamTable from '@/components/live-strategy-assistance/LiveStreamer';
import HeaderBox from "@/components/HeaderBox";
import RunScript from '@/components/live-strategy-assistance/RunScript';

const Page = () => {


  return (
    <section className="home">
      <div className="home-content">
        <header className="home-header">
          <HeaderBox
            type="greeting"
            title="Live Strategy Assistance"
            subtext="Keeps you on track"
          />
        </header>
        <div className="flex flex-col items-start">
  <RunScript />
</div>
        {/* Live Stream Data Section */}
        <LivestreamTable />

      </div>
    </section>
  );
};


export default Page;