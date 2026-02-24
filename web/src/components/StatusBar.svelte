<script>
  import { status, pipelineDone, connected } from '../lib/socket.js'
</script>

<div class="statusbar">
  <div class="conn" class:online={$connected}>
    {$connected ? '● онлайн' : '○ офлайн'}
  </div>

  {#if $status}
    <div class="pipeline">
      {#if $status.phase}
        <span class="stage">{$status.phase}</span>
      {/if}
      {#if $status.total > 0}
        <div class="progress-wrap">
          <div class="progress-bar" style="width:{($status.step/$status.total*100).toFixed(0)}%"></div>
        </div>
        <span class="steps">{$status.step}/{$status.total}</span>
      {/if}
      {#if $status.description}
        <span class="desc">{$status.description}</span>
      {/if}
      {#if $status.status}
        <span class="step-status">{$status.status}</span>
      {/if}
    </div>
  {/if}

  {#if $pipelineDone}
    <div class="done" class:ok={$pipelineDone.status === 'completed' || $pipelineDone.status === 'success'}
                      class:warn={$pipelineDone.status === 'partial' || $pipelineDone.status === 'partial_success'}
                      class:err={!['completed','success','partial','partial_success'].includes($pipelineDone.status)}>
      {$pipelineDone.status}
    </div>
  {/if}
</div>

<style>
  .statusbar {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: .4rem 1rem;
    background: #181825;
    border-bottom: 1px solid #313244;
    font-size: .78rem;
    min-height: 2rem;
    flex-wrap: wrap;
  }
  .conn { color: #6c7086; }
  .conn.online { color: #a6e3a1; }

  .pipeline {
    display: flex;
    align-items: center;
    gap: .5rem;
    color: #cdd6f4;
  }
  .stage { color: #89b4fa; font-weight: 600; }
  .steps { color: #6c7086; }
  .desc  { color: #bac2de; max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .step-status { color: #a6e3a1; font-weight: 500; }

  .progress-wrap {
    width: 80px;
    height: 4px;
    background: #313244;
    border-radius: 2px;
    overflow: hidden;
  }
  .progress-bar {
    height: 100%;
    background: #89b4fa;
    transition: width .3s;
  }

  .done {
    padding: .15rem .6rem;
    border-radius: 4px;
    font-weight: 600;
    font-size: .75rem;
  }
  .done.ok   { background: #a6e3a1; color: #1e1e2e; }
  .done.warn { background: #f9e2af; color: #1e1e2e; }
  .done.err  { background: #f38ba8; color: #1e1e2e; }
</style>
