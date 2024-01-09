import pickle as pkl
heatmap = True

with open('./data/state/jt_meets_state.pkl', 'rb') as f:
    jt = pkl.load(f)

jt = jt['matrix']
jt.to_csv('output/jt_matrix.csv')

with open('./data/state/jj_meets_state.pkl', 'rb') as f:
    jj = pkl.load(f)

jj = jj['matrix']
jj.to_csv('output/jj_matrix.csv')

if heatmap:
    import seaborn as sns
    import matplotlib.pyplot as plt
    plt.rcParams["figure.figsize"] = (20,20)
    sns.set(font='Ubuntu')

    graph = sns.heatmap(jt, cmap='rocket_r', vmin=0, vmax=5)
    fig = graph.get_figure()
    plt.title(f'Sum of squares: {(jt**2).sum().sum()}')
    fig.savefig('output/jt_matrix.png')
    plt.clf()

    graph = sns.heatmap(jj, cmap='rocket_r', vmin=0, vmax=5)
    fig = graph.get_figure()
    plt.title(f'Sum of squares: {(jj**2).sum().sum()}')
    fig.savefig('output/jj_matrix.png')    


