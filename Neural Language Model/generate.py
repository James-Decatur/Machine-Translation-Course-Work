'''
This script is used to generate new sentences from the trained models
'''

import argparse
import data
import torch

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='PyTorch Wikitext-2 Language Model')
    parser.add_argument('--data', type=str, default='./data/wikitext-2',
                        help='location of the data corpus')
    parser.add_argument('--checkpoint', type=str, default='/local/kurs/mt/nlm4assign3.pt',
                        help='model checkpoint to use')
    parser.add_argument('--outf', type=str, default='generated.txt',
                        help='output file for generated text')
    parser.add_argument('--words', type=int, default='1000',
                        help='number of words to generate')
    parser.add_argument('--seed', type=int, default=1111,
                        help='random seed')
    parser.add_argument('--cuda', action='store_true',
                        help='use CUDA')
    parser.add_argument('--temperature', type=float, default=1.0,
                        help='temperature - higher will increase diversity')
    parser.add_argument('--log-interval', type=int, default=100,
                        help='reporting interval')
    args = parser.parse_args()

    # set the random seed manually for reproducibility
    # for both cpu and gpu
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        if not args.cuda:
            print("WARNING: you have GPU devices, you should run with --cuda")
        else:
            torch.cuda.manual_seed(args.seed)

    device = torch.device("cuda" if args.cuda else "cpu")

    if args.temperature < 1e-3:
        parser.error("temperature has to be greater or equal to 1e-3")

    with open(args.checkpoint, 'rb') as f:
        model = torch.load(f, map_location=torch.device('cpu')).to(device)

    # set to evaluation mode (non-training)
    model.eval()

    corpus = data.Corpus(args.data)
    vocab_size = len(corpus.dictionary)
    hidden = model.init_hidden(1)
    input = torch.randint(vocab_size, (1, 1), dtype=torch.long).to(device)

    with open(args.outf, 'w') as outf:
        with torch.no_grad(): # no tracking history
            for i in range(args.words):
                output, hidden = model(input, hidden)
                word_weights = output.squeeze().div(args.temperature).exp().cpu()
                word_idx = torch.multinomial(word_weights, 1)[0]
                input.fill_(word_idx)

                word = corpus.dictionary.idx2word[word_idx]

                outf.write(word + ('\n' if i % 20 == 19 else ' '))

                if i % args.log_interval == 0:
                    print('| Generated {}/{} words'.format(i, args.words))
