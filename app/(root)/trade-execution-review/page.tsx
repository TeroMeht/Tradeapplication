import { TradelogDropBox } from '@/components/trade-execution-review/TradelogDropBox'
import HeaderBox from '@/components/HeaderBox'

const TradeExecutionReview = () => {

  return (
    <section className="home">
      <div className="home-content">
          <header className="home-header">
            <HeaderBox
              type="greeting"
              title="Trade Execution Review"
              subtext="How did you do and how are you going to improve that?"
            />
          </header>

          <div className="page-container">
              <TradelogDropBox />
          </div>
      </div>
    </section>
  )
}

export default TradeExecutionReview